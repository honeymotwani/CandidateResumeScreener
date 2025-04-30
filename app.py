from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

from services.job_analyzer import JobAnalyzer
from services.resume_processor import ResumeProcessor
from services.candidate_evaluator import CandidateEvaluator
from utils.file_utils import allowed_file, create_directories, save_results_to_csv
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, SECRET_KEY, GOOGLE_API_KEY

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.secret_key = SECRET_KEY

# Create necessary directories
create_directories([
    os.path.join(UPLOAD_FOLDER, 'job_descriptions'),
    os.path.join(UPLOAD_FOLDER, 'resumes'),
    os.path.join(UPLOAD_FOLDER, 'results')
])

# Initialize services
job_analyzer = JobAnalyzer(GOOGLE_API_KEY)
resume_processor = ResumeProcessor()
candidate_evaluator = CandidateEvaluator(GOOGLE_API_KEY)

# Add context processor for current year
@app.context_processor
def inject_now():
    return {'now': datetime.now}

@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')

@app.route('/job_description', methods=['GET', 'POST'])
def job_description():
    """Handle job description input"""
    if request.method == 'POST':
        # Get job description from form
        job_text = request.form.get('job_text', '')
        
        if not job_text:
            flash('Please enter a job description', 'danger')
            return redirect(request.url)
        
        # Create a unique session ID for this screening
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        # Create session directories
        session_dir = os.path.join(UPLOAD_FOLDER, session_id)
        job_dir = os.path.join(session_dir, 'job_descriptions')
        os.makedirs(job_dir, exist_ok=True)
        
        # Save job description to a text file
        job_filename = f"job_description_{session_id}.txt"
        job_path = os.path.join(job_dir, job_filename)
        with open(job_path, 'w', encoding='utf-8') as f:
            f.write(job_text)
        
        session['job_path'] = job_path
        session['job_description'] = job_text
        
        # Process job description to generate criteria
        try:
            criteria = job_analyzer.generate_criteria(job_text)
            session['criteria'] = criteria
            return redirect(url_for('set_criteria'))
        except Exception as e:
            flash(f'Error analyzing job description: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('job_description.html')

@app.route('/criteria', methods=['GET', 'POST'])
def set_criteria():
    """Handle setting priorities for evaluation criteria"""
    if 'criteria' not in session:
        flash('Please enter a job description first', 'warning')
        return redirect(url_for('job_description'))
    
    criteria = session['criteria']
    
    if request.method == 'POST':
        # Get selected criteria and their priorities
        selected_criteria = []
        priorities = {}
        
        for criterion in criteria:
            checkbox_key = f'criterion_{criterion.replace(" ", "_")}'
            priority_key = f'priority_{criterion.replace(" ", "_")}'
            
            if checkbox_key in request.form:
                selected_criterion = criterion
                selected_criteria.append(selected_criterion)
                
                if priority_key in request.form:
                    try:
                        priority = int(request.form[priority_key])
                        if 1 <= priority <= 10:
                            priorities[selected_criterion] = priority
                        else:
                            flash(f'Priority for {selected_criterion} must be between 1 and 10', 'warning')
                            return redirect(request.url)
                    except ValueError:
                        flash(f'Invalid priority value for {selected_criterion}', 'warning')
                        return redirect(request.url)
        
        if not selected_criteria:
            flash('Please select at least one criterion', 'warning')
            return redirect(request.url)
        
        if len(priorities) != len(selected_criteria):
            flash('Please set priorities for all selected criteria', 'warning')
            return redirect(request.url)
        
        session['selected_criteria'] = selected_criteria
        session['priorities'] = priorities
        
        return redirect(url_for('upload_resumes'))
    
    return render_template('criteria.html', criteria=criteria)

@app.route('/upload_resumes', methods=['GET', 'POST'])
def upload_resumes():
    """Handle resume uploads"""
    if 'priorities' not in session:
        flash('Please set criteria priorities first', 'warning')
        return redirect(url_for('set_criteria'))
    
    if request.method == 'POST':
        # Check if at least one resume is provided
        if 'resumes' not in request.files:
            flash('No resume files provided', 'danger')
            return redirect(request.url)
        
        resume_files = request.files.getlist('resumes')
        if len(resume_files) == 0 or resume_files[0].filename == '':
            flash('No resume files selected', 'danger')
            return redirect(request.url)
        
        # Get session data
        session_id = session.get('session_id')
        if not session_id:
            flash('Session expired. Please start over.', 'danger')
            return redirect(url_for('job_description'))
        
        # Create resume directory
        session_dir = os.path.join(UPLOAD_FOLDER, session_id)
        resume_dir = os.path.join(session_dir, 'resumes')
        os.makedirs(resume_dir, exist_ok=True)
        
        # Save resumes
        resume_paths = []
        for resume_file in resume_files:
            if resume_file and allowed_file(resume_file.filename, ALLOWED_EXTENSIONS):
                resume_filename = secure_filename(resume_file.filename)
                resume_path = os.path.join(resume_dir, resume_filename)
                resume_file.save(resume_path)
                resume_paths.append(resume_path)
        
        if not resume_paths:
            flash('No valid resume files uploaded', 'danger')
            return redirect(request.url)
        
        session['resume_paths'] = resume_paths
        
        # Process resumes
        job_description = session['job_description']
        selected_criteria = session['selected_criteria']
        priorities = session['priorities']
        
        processed_resumes = {}
        for resume_path in resume_paths:
            candidate_name = os.path.basename(resume_path).split('.')[0]
            resume_text = resume_processor.extract_text(resume_path)
            processed_resumes[candidate_name] = resume_text
        
        # Evaluate candidates
        try:
            results = candidate_evaluator.evaluate_candidates(
                job_description,
                selected_criteria,
                priorities,
                processed_resumes
            )
            
            session['results'] = results
            
            # Save results to CSV
            results_dir = os.path.join(UPLOAD_FOLDER, 'results', session_id)
            os.makedirs(results_dir, exist_ok=True)
            
            output_file = os.path.join(results_dir, 'evaluation_results.csv')
            sorted_results = sorted(
                [(candidate, data) for candidate, data in results.items()],
                key=lambda x: x[1]['overall_score'],
                reverse=True
            )
            save_results_to_csv(sorted_results, priorities, output_file)
            session['results_file'] = output_file
            
            return redirect(url_for('show_results'))
        except Exception as e:
            flash(f'Error evaluating candidates: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('upload_resumes.html')

@app.route('/results')
def show_results():
    """Display evaluation results"""
    if 'results' not in session:
        flash('Please complete the evaluation process first', 'warning')
        return redirect(url_for('job_description'))
    
    results = session['results']
    priorities = session.get('priorities', {})
    criteria = session.get('selected_criteria', [])
    
    # Sort candidates by overall score
    sorted_results = sorted(
        [(candidate, data) for candidate, data in results.items()],
        key=lambda x: x[1]['overall_score'],
        reverse=True
    )
    
    return render_template(
        'results.html',
        results=sorted_results,
        priorities=priorities,
        criteria=criteria,
        results_file=session.get('results_file', '')
    )

@app.route('/download_results')
def download_results():
    """Download results as CSV"""
    if 'results_file' not in session:
        flash('No results available to download', 'warning')
        return redirect(url_for('index'))
    
    results_file = session['results_file']
    if not os.path.exists(results_file):
        flash('Results file not found', 'warning')
        return redirect(url_for('index'))
    
    return send_file(
        results_file,
        as_attachment=True,
        download_name='resume_evaluation_results.csv',
        mimetype='text/csv'
    )

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    flash('File too large. Maximum file size is 16MB.', 'danger')
    return redirect(url_for('upload_resumes')), 413

@app.errorhandler(500)
def internal_server_error(error):
    """Handle internal server error"""
    flash('An error occurred while processing your request. Please try again.', 'danger')
    return render_template('index.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
