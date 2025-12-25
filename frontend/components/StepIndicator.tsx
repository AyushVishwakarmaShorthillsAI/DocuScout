'use client'

interface StepIndicatorProps {
    currentStep: number
    completedSteps: Set<number>
}

const steps = [
    { id: 1, title: "Extracting Clauses", description: "Analyzing contract structure" },
    { id: 2, title: "Researching Amendments", description: "Checking for legal updates" },
    { id: 3, title: "Analyzing Risks", description: "Generating compliance report" }
]

export default function StepIndicator({ currentStep, completedSteps }: StepIndicatorProps) {
    const getStepStatus = (stepId: number) => {
        if (completedSteps.has(stepId)) return 'complete'
        if (currentStep === stepId) return 'in-progress'
        return 'pending'
    }

    const getStepIcon = (stepId: number) => {
        if (completedSteps.has(stepId)) return '✓'
        if (currentStep === stepId) return '⏳'
        return stepId.toString()
    }

    return (
        <div className="step-indicator">
            {steps.map((step, index) => (
                <div key={step.id}>
                    <div className={`step step-${getStepStatus(step.id)}`}>
                        <div className="step-icon">
                            {getStepIcon(step.id)}
                        </div>
                        <div className="step-content">
                            <div className="step-title">{step.title}</div>
                            <div className="step-description">{step.description}</div>
                        </div>
                    </div>
                    {index < steps.length - 1 && (
                        <div className={`step-connector ${currentStep > step.id || completedSteps.has(step.id) ? 'active' : ''}`} />
                    )}
                </div>
            ))}
        </div>
    )
}
