/**
 * Resume Screener - Main JavaScript
 * Provides interactive features for the resume screening application
 */

document.addEventListener("DOMContentLoaded", () => {
    // Initialize all components
    initFileUpload()
    initPrioritySliders()
    initFormValidation()
    initCandidateSelection()
    initTooltips()
    initProgressBars()
  })
  
  /**
   * Initialize file upload functionality
   */
  function initFileUpload() {
    // File upload preview for job description
    const jobDescriptionInput = document.getElementById("job_description")
    if (jobDescriptionInput) {
      jobDescriptionInput.addEventListener("change", function () {
        updateFilePreview(this, "job-file-preview")
      })
    }
  
    // File upload preview for resumes
    const resumesInput = document.getElementById("resumes")
    if (resumesInput) {
      resumesInput.addEventListener("change", function () {
        const fileCount = this.files.length
        const fileList = document.createElement("div")
        fileList.className = "mt-2"
  
        if (fileCount > 0) {
          const fileHeader = document.createElement("p")
          fileHeader.textContent = `Selected ${fileCount} file(s):`
          fileList.appendChild(fileHeader)
  
          const fileNames = document.createElement("ul")
          fileNames.className = "list-group"
  
          for (let i = 0; i < fileCount; i++) {
            const item = document.createElement("li")
            item.className = "list-group-item"
            item.textContent = this.files[i].name
            fileNames.appendChild(item)
          }
  
          fileList.appendChild(fileNames)
        }
  
        // Remove previous list if exists
        const previousList = this.parentNode.querySelector("div.mt-2")
        if (previousList) {
          previousList.remove()
        }
  
        // Add new list
        if (fileCount > 0) {
          this.parentNode.appendChild(fileList)
        }
      })
    }
  
    // Drag and drop functionality
    const dropZones = document.querySelectorAll(".file-upload")
    dropZones.forEach((zone) => {
      zone.addEventListener("dragover", function (e) {
        e.preventDefault()
        this.classList.add("border-primary")
      })
  
      zone.addEventListener("dragleave", function (e) {
        e.preventDefault()
        this.classList.remove("border-primary")
      })
  
      zone.addEventListener("drop", function (e) {
        e.preventDefault()
        this.classList.remove("border-primary")
  
        const input = this.querySelector('input[type="file"]')
        if (input) {
          input.files = e.dataTransfer.files
  
          // Trigger change event
          const event = new Event("change", { bubbles: true })
          input.dispatchEvent(event)
        }
      })
    })
  }
  
  /**
   * Update file preview
   * @param {HTMLInputElement} input - File input element
   * @param {string} previewId - ID of preview element
   */
  function updateFilePreview(input, previewId) {
    const preview = document.getElementById(previewId)
    if (!preview) return
  
    if (input.files && input.files.length > 0) {
      const fileName = input.files[0].name
      preview.textContent = fileName
      preview.classList.remove("d-none")
    } else {
      preview.textContent = ""
      preview.classList.add("d-none")
    }
  }
  
  /**
   * Initialize priority sliders
   */
  function initPrioritySliders() {
    const priorityInputs = document.querySelectorAll('input[type="number"][min="1"][max="10"]')
    priorityInputs.forEach((input) => {
      input.addEventListener("change", function () {
        const value = Number.parseInt(this.value)
        if (value >= 1 && value <= 10) {
          // Change background color based on priority
          const alpha = value / 10
          this.style.backgroundColor = `rgba(37, 99, 235, ${alpha})`
          this.style.color = value > 5 ? "white" : "black"
        } else {
          this.style.backgroundColor = ""
          this.style.color = ""
        }
      })
  
      // Trigger change event to apply initial styling
      input.dispatchEvent(new Event("change"))
    })
  }
  
  /**
   * Initialize form validation
   */
  function initFormValidation() {
    const forms = document.querySelectorAll(".needs-validation")
  
    Array.from(forms).forEach((form) => {
      form.addEventListener(
        "submit",
        (event) => {
          if (!form.checkValidity()) {
            event.preventDefault()
            event.stopPropagation()
          }
  
          form.classList.add("was-validated")
        },
        false,
      )
    })
  }
  
  /**
   * Initialize candidate selection in results table
   */
  function initCandidateSelection() {
    const candidateRows = document.querySelectorAll(".candidate-row")
    const candidateDetails = document.getElementById("candidate-details")
  
    candidateRows.forEach((row) => {
      row.addEventListener("click", function () {
        // Remove selected class from all rows
        candidateRows.forEach((r) => r.classList.remove("selected"))
  
        // Add selected class to clicked row
        this.classList.add("selected")
  
        // Update candidate details if available
        if (candidateDetails) {
          const candidateName = this.getAttribute("data-candidate")
          const overallScore = this.getAttribute("data-score")
  
          // Update details
          const nameElement = candidateDetails.querySelector(".candidate-name")
          const scoreElement = candidateDetails.querySelector(".candidate-score")
  
          if (nameElement) nameElement.textContent = candidateName
          if (scoreElement) {
            scoreElement.textContent = `${overallScore}%`
  
            // Update score color
            const score = Number.parseFloat(overallScore)
            if (score >= 80) {
              scoreElement.className = "candidate-score text-success"
            } else if (score >= 60) {
              scoreElement.className = "candidate-score text-warning"
            } else {
              scoreElement.className = "candidate-score text-danger"
            }
          }
  
          // Show details
          candidateDetails.classList.remove("d-none")
        }
      })
    })
  }
  
  /**
   * Initialize tooltips
   */
  function initTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    if (tooltipTriggerList.length > 0) {
      // Declare bootstrap variable
      const bootstrap = window.bootstrap
  
      Array.from(tooltipTriggerList).forEach((tooltipTriggerEl) => {
        new bootstrap.Tooltip(tooltipTriggerEl)
      })
    }
  }
  
  /**
   * Initialize progress bars
   */
  function initProgressBars() {
    const progressBars = document.querySelectorAll(".progress-bar")
    progressBars.forEach((bar) => {
      const value = bar.getAttribute("aria-valuenow")
      bar.style.width = `${value}%`
  
      // Set color based on value
      if (value >= 80) {
        bar.classList.add("bg-success")
      } else if (value >= 60) {
        bar.classList.add("bg-warning")
      } else {
        bar.classList.add("bg-danger")
      }
    })
  }
  
  /**
   * Format a number as a percentage
   * @param {number} value - Value to format
   * @param {number} decimals - Number of decimal places
   * @returns {string} Formatted percentage
   */
  function formatPercentage(value, decimals = 2) {
    return value.toFixed(decimals) + "%"
  }
  
  /**
   * Show loading spinner
   * @param {string} containerId - ID of container element
   * @param {string} message - Loading message
   */
  function showLoading(containerId, message = "Processing...") {
    const container = document.getElementById(containerId)
    if (!container) return
  
    const spinner = document.createElement("div")
    spinner.className = "text-center my-5"
    spinner.innerHTML = `
          <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2">${message}</p>
      `
  
    container.innerHTML = ""
    container.appendChild(spinner)
  }
  
  /**
   * Hide loading spinner
   * @param {string} containerId - ID of container element
   */
  function hideLoading(containerId) {
    const container = document.getElementById(containerId)
    if (!container) return
  
    const spinner = container.querySelector(".spinner-border")
    if (spinner) {
      spinner.parentNode.remove()
    }
  }
  
  /**
   * Show alert message
   * @param {string} containerId - ID of container element
   * @param {string} message - Alert message
   * @param {string} type - Alert type (success, danger, warning, info)
   * @param {boolean} dismissible - Whether the alert can be dismissed
   */
  function showAlert(containerId, message, type = "info", dismissible = true) {
    const container = document.getElementById(containerId)
    if (!container) return
  
    const alert = document.createElement("div")
    alert.className = `alert alert-${type} ${dismissible ? "alert-dismissible fade show" : ""}`
    alert.setAttribute("role", "alert")
  
    alert.innerHTML = message
  
    if (dismissible) {
      alert.innerHTML += `
              <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
          `
    }
  
    container.appendChild(alert)
  }
  