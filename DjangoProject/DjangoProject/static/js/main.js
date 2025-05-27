// Main JavaScript file for the survey application

document.addEventListener("DOMContentLoaded", () => {
  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl))

  // Initialize popovers
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
  popoverTriggerList.map((popoverTriggerEl) => new bootstrap.Popover(popoverTriggerEl))

  // Auto-dismiss alerts after 5 seconds
  setTimeout(() => {
    const alerts = document.querySelectorAll(".alert:not(.alert-permanent)")
    alerts.forEach((alert) => {
      const bsAlert = new bootstrap.Alert(alert)
      bsAlert.close()
    })
  }, 5000)

  // Conditional logic for questions (if implemented)
  setupConditionalLogic()
})

// Function to handle conditional logic between questions
function setupConditionalLogic() {
  const conditionalQuestions = document.querySelectorAll("[data-conditional-logic]")

  conditionalQuestions.forEach((question) => {
    const logic = JSON.parse(question.dataset.conditionalLogic)

    if (!logic || !logic.conditions) return

    // Find the trigger questions
    logic.conditions.forEach((condition) => {
      const triggerInput = document.querySelector(`[name="question_${condition.question_id}"]`)

      if (!triggerInput) return

      // Add event listener to the trigger
      if (triggerInput.type === "radio" || triggerInput.type === "checkbox") {
        const radioGroup = document.querySelectorAll(`[name="${triggerInput.name}"]`)
        radioGroup.forEach((radio) => {
          radio.addEventListener("change", () => evaluateCondition(logic, question))
        })
      } else {
        triggerInput.addEventListener("change", () => evaluateCondition(logic, question))
        triggerInput.addEventListener("input", () => evaluateCondition(logic, question))
      }

      // Initial evaluation
      evaluateCondition(logic, question)
    })
  })
}

// Function to evaluate conditional logic
function evaluateCondition(logic, questionElement) {
  let shouldShow = true

  logic.conditions.forEach((condition) => {
    const inputs = document.querySelectorAll(`[name="question_${condition.question_id}"]`)

    if (!inputs.length) return

    // For radio buttons and checkboxes
    if (inputs[0].type === "radio" || inputs[0].type === "checkbox") {
      const selectedValues = Array.from(inputs)
        .filter((input) => input.checked)
        .map((input) => input.value)

      if (condition.operator === "equals") {
        if (!selectedValues.includes(condition.value.toString())) {
          shouldShow = false
        }
      } else if (condition.operator === "not_equals") {
        if (selectedValues.includes(condition.value.toString())) {
          shouldShow = false
        }
      }
    }
    // For text inputs, selects, etc.
    else {
      const value = inputs[0].value

      if (condition.operator === "equals") {
        if (value !== condition.value) {
          shouldShow = false
        }
      } else if (condition.operator === "not_equals") {
        if (value === condition.value) {
          shouldShow = false
        }
      } else if (condition.operator === "contains") {
        if (!value.includes(condition.value)) {
          shouldShow = false
        }
      } else if (condition.operator === "not_contains") {
        if (value.includes(condition.value)) {
          shouldShow = false
        }
      }
    }
  })

  // Apply visibility
  if (shouldShow) {
    questionElement.style.display = ""
  } else {
    questionElement.style.display = "none"
  }
}
