document.addEventListener('DOMContentLoaded', () => {
    // Initial State: All sections are visible in the layout, but assessment form is hidden by css class '.hidden' initially
});

let selectedMode = 'balanced';
let uploadedResumeName = null;

async function uploadResume() {
    const fileInput = document.getElementById('resume-upload');
    const file = fileInput.files[0];
    if (!file) {
        alert("Please select a file first.");
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const btn = document.querySelector('#resume-section button');
        const originalText = btn.textContent;
        btn.textContent = "Uploading...";
        btn.disabled = true;

        const response = await fetch('/api/upload_resume', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error("Upload failed");

        const data = await response.json();
        uploadedResumeName = data.filename;
        alert("Resume uploaded successfully! We will use it for your assessment.");

        btn.textContent = "Uploaded ✓";

    } catch (error) {
        console.error("Error uploading resume:", error);
        alert("Failed to upload resume.");
        document.querySelector('#resume-section button').textContent = "Upload Resume";
        document.querySelector('#resume-section button').disabled = false;
    }
}

async function startAssessment(mode) {
    selectedMode = mode;
    console.log(`Starting ${mode} assessment...`);

    try {
        // 1. Fetch Questions
        const response = await fetch(`/api/questions/${mode}`);
        if (!response.ok) throw new Error("Failed to load questions");
        const questions = await response.json();

        // 2. Render Questions
        const container = document.getElementById('questions-container');
        container.innerHTML = ''; // Clear loading text

        questions.forEach((q, index) => {
            const questionDiv = document.createElement('div');
            questionDiv.className = "mb-6 p-4 border rounded bg-white shadow-sm";

            let inputHtml = '';
            if (q.type === 'mcq') {
                inputHtml = `<div class="space-y-2 mt-2">`;
                q.options.forEach(opt => {
                    inputHtml += `
                    <label class="flex items-center cursor-pointer">
                        <input type="radio" name="q_${q.id}" value="${opt}" class="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500" required>
                        <span class="ml-2 text-gray-700">${opt}</span>
                    </label>`;
                });
                inputHtml += `</div>`;
            } else if (q.type === 'text') {
                inputHtml = `<textarea name="q_${q.id}" class="w-full mt-2 p-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500" rows="3" placeholder="Type your answer here..." required></textarea>`;
            }

            questionDiv.innerHTML = `
                <p class="font-bold text-gray-800 mb-1">${index + 1}. ${q.text}</p>
                ${inputHtml}
            `;
            container.appendChild(questionDiv);
        });

        // 3. Switch View
        document.getElementById('mode-selection').style.display = 'none';

        // Also hide resume section to focus on questions
        const resumeSection = document.getElementById('resume-section');
        if (resumeSection) resumeSection.style.display = 'none';

        const assessmentSection = document.getElementById('detailed-assessment');
        assessmentSection.classList.remove('hidden'); // Show container
        assessmentSection.style.display = 'block'; // Ensure display block if previously hidden by style

        // Update Title
        const titleElement = assessmentSection.querySelector('h2');
        titleElement.textContent = `${mode.charAt(0).toUpperCase() + mode.slice(1)} Assessment`;

        assessmentSection.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        console.error("Error:", error);
        alert("Could not load assessment. Please make sure backend is running.");
    }
}

async function submitAssessment() {
    const form = document.getElementById('assessment-form');
    const formData = new FormData(form);
    const answers = {};

    // Collect answers
    for (let [key, value] of formData.entries()) {
        answers[key] = value;
    }

    const requestData = {
        mode: selectedMode,
        answers: answers,
        resume_filename: uploadedResumeName
    };

    try {
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = "Analyzing Profile...";
        submitBtn.disabled = true;

        const response = await fetch('/api/assess', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) throw new Error("Analysis failed");

        const data = await response.json();
        updateReportUI(data);

        // Show Report, Hide Assessment
        document.getElementById('detailed-assessment').style.display = 'none';
        const reportSection = document.getElementById('report');
        reportSection.classList.remove('hidden');
        reportSection.style.display = 'block';
        reportSection.scrollIntoView({ behavior: 'smooth' });

        submitBtn.textContent = originalText;
        submitBtn.disabled = false;

    } catch (error) {
        console.error("Error:", error);
        alert("Failed to submit assessment. Please try again.");
    }
}

function updateReportUI(data) {
    // 1. Update Readiness Score
    // Using generic selection or creating element if missing
    let scoreEl = document.getElementById('readiness-score-display');
    if (!scoreEl) {
        // Try to find the progress circle span
        const circleSpan = document.querySelector('.progress-circle span');
        if (circleSpan) {
            scoreEl = circleSpan;
        } else {
            // Fallback: insert after H2
            const h2 = document.querySelector('#report h2');
            if (h2) {
                scoreEl = document.createElement('div');
                scoreEl.id = 'readiness-score-display';
                scoreEl.className = "text-4xl font-bold text-center text-blue-800 my-4";
                h2.after(scoreEl);
            }
        }
    }
    if (scoreEl && data.readiness_score) scoreEl.textContent = `${data.readiness_score}%`;

    // Update PDF Link
    const pdfBtn = document.querySelector('#report a[download]');
    if (pdfBtn && data.pdf_url) {
        pdfBtn.href = data.pdf_url;
    }

    // Strengths (Green list)
    const strengthsList = document.querySelector('#report ul.text-green-700');
    if (strengthsList) {
        strengthsList.innerHTML = data.strengths.map(s => `<li>${s}</li>`).join('');
    }

    // Gaps (Red list)
    const gapsList = document.querySelector('#report ul.text-red-700');
    if (gapsList) {
        gapsList.innerHTML = data.gaps.map(g => `<li>${g}</li>`).join('');
    }

    // Action Plan
    const actionPlanList = document.querySelector('#report ol');
    if (actionPlanList) {
        actionPlanList.innerHTML = data.action_plan.map(plan => `<li class="text-gray-700">${plan}</li>`).join('');
    }

    // Job Recommendations
    const jobsContainer = document.querySelector('#report .space-y-4');
    if (jobsContainer && data.job_recommendations) {
        jobsContainer.innerHTML = data.job_recommendations.map(job => `
            <div class="flex justify-between items-center p-4 border rounded-lg hover:shadow-md transition">
                <div>
                    <h4 class="text-lg font-semibold text-blue-700">${job.role}</h4>
                    <p class="text-gray-600 font-medium">${job.company}</p>
                    <p class="text-sm text-gray-500">${job.location} • Match: <span class="text-green-600 font-bold">${job.match}</span></p>
                </div>
                <button class="py-2 px-4 bg-gray-100 text-blue-600 font-semibold rounded-lg hover:bg-gray-200">View</button>
            </div>
        `).join('');
    }

    // Email Draft
    const emailTextarea = document.getElementById('email-draft-output');
    if (emailTextarea) {
        emailTextarea.value = data.email_draft;
    }
}
