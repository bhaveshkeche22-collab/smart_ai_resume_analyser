(function () {
    "use strict";

    /*
    ============================================================
    AI RESUME ANALYZER
    Dashboard JavaScript
    ============================================================

    Handles:
    - Resume upload
    - Resume profile
    - ATS analysis
    - Analysis history
    - Evidence detector
    - Recommended jobs
    - Job search
    - Loading states
    - Error handling
    ============================================================
    */


    /* =========================================================
       HELPERS
    ========================================================= */

    const $ = (id) => document.getElementById(id);

    window.resumeUploadData =
        window.resumeUploadData || null;

    window.resumeAnalysis =
        window.resumeAnalysis || null;

    window.analysisResult =
        window.analysisResult || null;

    window.currentAnalysis =
        window.currentAnalysis || null;


    function escapeHtml(value) {

        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    }


    function percentage(value) {

        return `${Number(value || 0).toFixed(1)}%`;

    }


    function formatText(value) {

        return escapeHtml(
            value || "Not detected"
        ).replace(/\n/g, "<br>");

    }


    function showToast(message, type = "info") {

        const existing =
            document.querySelector(
                ".resume-toast"
            );

        if (existing) {
            existing.remove();
        }


        const toast =
            document.createElement("div");

        toast.className =
            `resume-toast resume-toast-${type}`;

        toast.innerHTML = `
            <i class="bi ${
                type === "success"
                    ? "bi-check-circle-fill"
                    : type === "danger"
                        ? "bi-exclamation-triangle-fill"
                        : "bi-info-circle-fill"
            }"></i>

            <span>
                ${escapeHtml(message)}
            </span>
        `;


        document.body.appendChild(toast);


        setTimeout(() => {

            toast.classList.add("hide");

            setTimeout(() => {
                toast.remove();
            }, 300);

        }, 3500);

    }


    async function fetchJson(
        url,
        options = {}
    ) {

        const response =
            await fetch(url, {
                ...options,
                credentials: "same-origin"
            });


        const contentType =
            response.headers.get(
                "content-type"
            ) || "";


        let data;


        if (
            contentType.includes(
                "application/json"
            )
        ) {

            data =
                await response.json();

        } else {

            throw new Error(
                `Server returned HTTP ${response.status}.`
            );

        }


        if (
            !response.ok ||
            data.success === false
        ) {

            throw new Error(
                data.message ||
                `Request failed with HTTP ${response.status}`
            );

        }


        return data;

    }



    /* =========================================================
       DOM REFERENCES
    ========================================================= */

    const resumeFile =
        $("resumeFile");

    const uploadCard =
        $("uploadCard");

    const selectedFile =
        $("selectedFile");

    const chooseFileButton =
        $("chooseFileButton");

    const analyzeButton =
        $("analyzeButton");

    const jobDescription =
        $("jobDescription");

    const charCount =
        $("charCount");

    const loadJobTemplate =
        $("loadJobTemplate");



    /* =========================================================
       JOB TEMPLATES
    ========================================================= */

    const JOB_TEMPLATES = {

        "Software Engineer":
            "We are looking for a Software Engineer with Python or Java, data structures and algorithms, SQL, REST APIs, Git, GitHub, testing, debugging, and software development experience. Strong problem solving and teamwork skills are required.",

        "Frontend Developer":
            "Frontend Developer with HTML, CSS, JavaScript, React, responsive UI development, REST API integration, Git and GitHub. Experience with modern web development and testing is preferred.",

        "Backend Developer":
            "Backend Developer with Python, Flask or FastAPI, SQL, MySQL or PostgreSQL, REST APIs, Git, authentication, database design, testing and deployment experience.",

        "Data Scientist":
            "Data Scientist with Python, SQL, Pandas, NumPy, Matplotlib, Scikit-learn, statistics, data analysis, machine learning, feature engineering, model evaluation and data visualization. Power BI or Tableau experience is useful.",

        "Machine Learning Engineer":
            "Machine Learning Engineer with Python, NumPy, Pandas, Scikit-learn, TensorFlow or PyTorch, machine learning, deep learning, model evaluation, APIs and deployment. Experience with Git and data pipelines is preferred.",

        "Data Analyst":
            "Data Analyst with SQL, Python, Pandas, Excel, Power BI or Tableau, statistics, data cleaning, exploratory data analysis, dashboards and data visualization. Strong communication and analytical skills are required.",

        "Full Stack Developer":
            "Full Stack Developer with HTML, CSS, JavaScript, React, Node.js, Python or Flask, SQL, REST APIs, Git and GitHub. Experience building responsive frontend and backend applications is preferred."

    };



    /* =========================================================
       FILE UPLOAD
    ========================================================= */

    function validateFile(file) {

        if (!file) {
            return false;
        }

        return (
            file.type === "application/pdf" ||
            file.name
                .toLowerCase()
                .endsWith(".pdf")
        );

    }


    function displayFile(file) {

        if (!selectedFile) {
            return;
        }


        selectedFile.innerHTML = `

            <div class="file-selected">

                <i class="bi bi-file-earmark-pdf"></i>

                <div>

                    <strong>
                        ${escapeHtml(file.name)}
                    </strong>

                    <small>
                        ${(file.size / 1024 / 1024).toFixed(2)}
                        MB
                    </small>

                </div>

                <i class="bi bi-check-circle-fill"></i>

            </div>

        `;


        if (uploadCard) {
            uploadCard.classList.add(
                "upload-success"
            );
        }

    }


    function handleFile(file) {

        if (!validateFile(file)) {

            if (selectedFile) {

                selectedFile.innerHTML = `

                    <div class="file-error">

                        <i class="bi bi-exclamation-circle"></i>

                        Please select a PDF resume.

                    </div>

                `;

            }


            if (resumeFile) {
                resumeFile.value = "";
            }


            return;

        }


        displayFile(file);

    }



    /* Choose file */

    if (
        chooseFileButton &&
        resumeFile
    ) {

        chooseFileButton.addEventListener(
            "click",
            () => resumeFile.click()
        );


        resumeFile.addEventListener(
            "change",
            () => {

                handleFile(
                    resumeFile.files[0]
                );

            }
        );

    }



    /* Drag & Drop */

    if (
        uploadCard &&
        resumeFile
    ) {

        uploadCard.addEventListener(
            "dragover",
            (event) => {

                event.preventDefault();

                uploadCard.classList.add(
                    "drag-active"
                );

            }
        );


        uploadCard.addEventListener(
            "dragleave",
            () => {

                uploadCard.classList.remove(
                    "drag-active"
                );

            }
        );


        uploadCard.addEventListener(
            "drop",
            (event) => {

                event.preventDefault();

                uploadCard.classList.remove(
                    "drag-active"
                );


                const file =
                    event.dataTransfer
                        .files[0];


                if (!file) {
                    return;
                }


                try {

                    const dataTransfer =
                        new DataTransfer();

                    dataTransfer.items.add(
                        file
                    );

                    resumeFile.files =
                        dataTransfer.files;

                } catch (_) {
                    // Browser may block direct assignment.
                }


                handleFile(file);

            }
        );

    }



    /* =========================================================
       JOB DESCRIPTION
    ========================================================= */

    if (
        jobDescription &&
        charCount
    ) {

        jobDescription.addEventListener(
            "input",
            () => {

                charCount.textContent =
                    jobDescription.value.length;

            }
        );

    }



    if (loadJobTemplate) {

        loadJobTemplate.addEventListener(
            "click",
            () => {

                const role =
                    $("jobRole")?.value || "";


                if (!role) {

                    showToast(
                        "Please select a job role first.",
                        "info"
                    );

                    return;

                }


                jobDescription.value =
                    JOB_TEMPLATES[role] || "";


                if (charCount) {

                    charCount.textContent =
                        jobDescription.value.length;

                }

            }
        );

    }



    /* =========================================================
       BUTTON LOADING
    ========================================================= */

    function setAnalyzeLoading(
        loading,
        text = "Analyzing..."
    ) {

        if (!analyzeButton) {
            return;
        }


        analyzeButton.disabled =
            loading;


        analyzeButton.innerHTML =
            loading

                ? `
                    <span
                        class="spinner-border spinner-border-sm me-2">
                    </span>

                    ${escapeHtml(text)}
                  `

                : `
                    <i class="bi bi-magic"></i>
                    Analyze Resume
                  `;

    }



    /* =========================================================
       UPLOAD RESUME
    ========================================================= */

    async function uploadResume() {

        const file =
            resumeFile?.files?.[0];


        if (!file) {

            throw new Error(
                "Please select your resume first."
            );

        }


        const formData =
            new FormData();

        formData.append(
            "resume",
            file
        );


        const data =
            await fetchJson(
                "/resume/upload",
                {
                    method: "POST",
                    body: formData
                }
            );


        window.resumeUploadData =
            data;


        return data;

    }



    /* =========================================================
       PROFILE
    ========================================================= */

    function renderProfile(data) {

        if (!data) {
            return;
        }


        const info =
            data.information || {};


        const name =
            info.name ||
            data.name ||
            "Not detected";


        const email =
            info.email ||
            data.email ||
            "Not detected";


        const phone =
            info.phone ||
            data.phone ||
            "Not detected";


        if ($("profileName")) {

            $("profileName").textContent =
                name;

        }


        if ($("profileEmail")) {

            $("profileEmail").textContent =
                email;

        }


        if ($("profilePhone")) {

            $("profilePhone").textContent =
                phone;

        }


        if ($("profileEducation")) {

            $("profileEducation").innerHTML =
                formatText(
                    info.education
                );

        }


        if ($("profileExperience")) {

            $("profileExperience").innerHTML =
                formatText(
                    info.experience
                );

        }


        if ($("profileProjects")) {

            $("profileProjects").innerHTML =
                formatText(
                    info.projects
                );

        }


        const skills =
            Array.isArray(
                data.skills
            )
                ? data.skills
                : Array.isArray(
                    info.skills
                )
                    ? info.skills
                    : [];


        if ($("profileSkills")) {

            $("profileSkills").innerHTML =
                skills.length

                    ? skills.map(
                        skill => `
                            <span class="skill-badge">
                                ${escapeHtml(skill)}
                            </span>
                        `
                    ).join("")

                    : `
                        <span class="result-empty">
                            No skills detected
                        </span>
                    `;

        }


        if ($("profileAvatar")) {

            $("profileAvatar").textContent =
                name
                    .trim()
                    .charAt(0)
                    .toUpperCase() || "U";

        }


        if ($("profileSection")) {

            $("profileSection").style.display =
                "block";

        }

    }



    /* =========================================================
       ANALYSIS LIST
    ========================================================= */

    function renderList(
        id,
        values,
        emptyText
    ) {

        const element = $(id);


        if (!element) {
            return;
        }


        const list =
            Array.isArray(values)
                ? values
                : [];


        element.innerHTML =

            list.length

                ? list.map(
                    value =>
                        `<span>
                            ${escapeHtml(value)}
                         </span>`
                ).join("")

                : `
                    <div class="result-empty">
                        ${escapeHtml(emptyText)}
                    </div>
                `;

    }



    /* =========================================================
       ANALYSIS RESULT
    ========================================================= */

    function renderAnalysis(
        data,
        scroll = true
    ) {

        if (!data) {
            return;
        }


        /*
        Preserve important data for
        Evidence Detector and Jobs.
        */

        const savedAnalysis = {

            ...data,

            resume_text:
                data.resume_text ||
                data.extracted_text ||
                window.resumeUploadData?.extracted_text ||
                window.resumeUploadData?.resume_text ||
                "",

            extracted_text:
                data.extracted_text ||
                data.resume_text ||
                window.resumeUploadData?.extracted_text ||
                window.resumeUploadData?.resume_text ||
                "",

            job_description:
                data.job_description ||
                data.jd_text ||
                jobDescription?.value ||
                "",

            jd_text:
                data.jd_text ||
                data.job_description ||
                jobDescription?.value ||
                "",

            missing_skills:
                Array.isArray(
                    data.missing_skills
                )
                    ? data.missing_skills
                    : []

        };


        window.resumeAnalysis =
            savedAnalysis;

        window.analysisResult =
            savedAnalysis;

        window.currentAnalysis =
            savedAnalysis;



        /* Score cards */

        if ($("atsScoreValue")) {

            $("atsScoreValue").textContent =
                percentage(
                    data.ats_score
                );

        }


        if ($("skillMatchValue")) {

            $("skillMatchValue").textContent =
                percentage(
                    data.skill_match_score
                );

        }


        if ($("similarityValue")) {

            $("similarityValue").textContent =
                percentage(
                    data.similarity_score
                );

        }


        if ($("qualityValue")) {

            $("qualityValue").textContent =
                percentage(
                    data.quality_score
                );

        }



        /* Status */

        if ($("atsStatus"))
            $("atsStatus").textContent =
                "Analyzed";


        if ($("matchStatus"))
            $("matchStatus").textContent =
                "Analyzed";


        if ($("similarityStatus"))
            $("similarityStatus").textContent =
                "Analyzed";


        if ($("qualityStatus"))
            $("qualityStatus").textContent =
                "Checked";



        /* Job information */

        if ($("resultJobTitle")) {

            $("resultJobTitle").textContent =
                data.job_title ||
                "Selected Job";

        }


        if ($("resultExperience")) {

            $("resultExperience").textContent =
                data.experience_level ||
                "Not specified";

        }



        /* Summary */

        const recommendation =
            data.recommendation || {};


        if ($("resultSummary")) {

            $("resultSummary").textContent =
                recommendation.summary ||
                "Analysis completed.";

        }



        /* Detailed scores */

        const scoreMap = {

            resultAtsScore:
                data.ats_score,

            resultSkillMatch:
                data.skill_match_score,

            resultSimilarity:
                data.similarity_score,

            resultEducation:
                data.education_score,

            resultProjects:
                data.project_score,

            resultExperienceScore:
                data.experience_score,

            resultKeywords:
                data.keyword_score,

            resultQuality:
                data.quality_score

        };


        Object.entries(
            scoreMap
        ).forEach(
            ([id, value]) => {

                if ($(id)) {

                    $(id).textContent =
                        percentage(value);

                }

            }
        );



        /* Skills */

        renderList(
            "matchedSkills",
            data.matched_skills,
            "No required skills matched."
        );


        renderList(
            "missingSkills",
            data.missing_skills,
            "No missing skills detected."
        );



        /* Recommendation */

        if ($("resultRecommendation")) {

            $("resultRecommendation").textContent =
                recommendation.summary ||
                "No recommendation available.";

        }


        if ($("resultSuggestions")) {

            const suggestions =
                Array.isArray(
                    recommendation.suggestions
                )
                    ? recommendation.suggestions
                    : [];


            $("resultSuggestions").innerHTML =
                suggestions.map(
                    suggestion =>
                        `<li>
                            ${escapeHtml(suggestion)}
                         </li>`
                ).join("");

        }


        if ($("recommendationProvider")) {

            $("recommendationProvider").textContent =

                recommendation.provider === "gemini"

                    ? "AI recommendation: Gemini"

                    : "Recommendation engine: local ATS analysis";

        }



        /* Show results */

        if ($("atsResultsSection")) {

            $("atsResultsSection").style.display =
                "block";


            if (scroll) {

                $("atsResultsSection")
                    .scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });

            }

        }

    }



    /* =========================================================
       RUN ANALYSIS
    ========================================================= */

    async function runAnalysis() {

        const jobTitle =
            $("jobRole")?.value.trim() || "";


        const experienceLevel =
            $("experienceLevel")
                ?.value.trim() || "";


        const description =
            jobDescription
                ?.value.trim() || "";


        if (!resumeFile?.files?.[0]) {

            throw new Error(
                "Please select a resume first."
            );

        }


        if (!jobTitle) {

            throw new Error(
                "Please select a target job."
            );

        }


        if (
            !description ||
            description.length < 30
        ) {

            throw new Error(
                "Please enter a complete job description or use the sample JD button."
            );

        }



        /* Upload */

        setAnalyzeLoading(
            true,
            "Uploading resume..."
        );


        const uploadData =
            await uploadResume();


        renderProfile(
            uploadData
        );



        /* Analysis */

        setAnalyzeLoading(
            true,
            "Calculating ATS score..."
        );


        const result =
            await fetchJson(
                "/analysis/analyze",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        resume_id:
                            uploadData.resume_id,

                        job_title:
                            jobTitle,

                        experience_level:
                            experienceLevel,

                        job_description:
                            description

                    })

                }
            );


        window.resumeUploadData =
            uploadData;


        renderAnalysis(
            result
        );


        /*
        IMPORTANT:
        Refresh jobs after analysis.
        */

        await loadRecommendedJobs();


        await loadHistory();


        showToast(
            "Resume analysis completed successfully.",
            "success"
        );

    }



    /* Analyze button */

    if (analyzeButton) {

        analyzeButton.addEventListener(
            "click",
            async () => {

                try {

                    await runAnalysis();

                } catch (error) {

                    console.error(
                        "Analysis error:",
                        error
                    );


                    showToast(
                        error.message ||
                        "Analysis failed.",
                        "danger"
                    );

                } finally {

                    setAnalyzeLoading(
                        false
                    );

                }

            }
        );

    }



    /* =========================================================
       HISTORY
    ========================================================= */

    async function loadHistory() {

        try {

            const data =
                await fetchJson(
                    "/analysis/history"
                );


            const container =
                $("historyContainer");


            if (!container) {
                return;
            }


            if (
                !Array.isArray(
                    data.analyses
                ) ||
                !data.analyses.length
            ) {

                container.innerHTML = `

                    <div class="empty-history">

                        <div class="history-icon">

                            <i class="bi bi-clock-history"></i>

                        </div>

                        <h4>
                            No analyses yet
                        </h4>

                        <p>
                            Your completed analyses will appear here.
                        </p>

                    </div>

                `;

                return;

            }


            container.innerHTML =
                data.analyses.map(
                    item => `

                    <div class="history-row">

                        <div>

                            <strong>
                                ${escapeHtml(
                                    item.job_title
                                )}
                            </strong>

                            <small>
                                ${
                                    item.created_at
                                        ? new Date(
                                            item.created_at
                                        ).toLocaleString()
                                        : ""
                                }
                            </small>

                        </div>


                        <div class="history-scores">

                            <span>
                                ATS
                                <b>
                                    ${percentage(
                                        item.ats_score
                                    )}
                                </b>
                            </span>

                            <span>
                                Match
                                <b>
                                    ${percentage(
                                        item.match_score
                                    )}
                                </b>
                            </span>

                            <span>
                                Similarity
                                <b>
                                    ${percentage(
                                        item.similarity_score
                                    )}
                                </b>
                            </span>

                            <span>
                                Quality
                                <b>
                                    ${percentage(
                                        item.quality_score
                                    )}
                                </b>
                            </span>

                        </div>

                    </div>

                `
                ).join("");

        } catch (error) {

            console.warn(
                "History could not be loaded:",
                error
            );

        }

    }



    /* =========================================================
       LATEST ANALYSIS
    ========================================================= */

    async function loadLatest() {

        try {

            const data =
                await fetchJson(
                    "/analysis/latest"
                );


            if (data) {

                renderAnalysis(
                    data,
                    false
                );

            }

        } catch (_) {

            /*
            Normal on first dashboard visit.
            */

        }

    }



    /* =========================================================
       EVIDENCE DETECTOR
    ========================================================= */

    function getCurrentAnalysis() {

        return (
            window.resumeAnalysis ||
            window.analysisResult ||
            window.currentAnalysis ||
            null
        );

    }


    async function getAnalysisForEvidence() {

        let analysis =
            getCurrentAnalysis();


        if (!analysis) {

            try {

                const latest =
                    await fetchJson(
                        "/analysis/latest"
                    );


                if (latest) {

                    renderAnalysis(
                        latest,
                        false
                    );

                    analysis =
                        getCurrentAnalysis();

                }

            } catch (error) {

                console.warn(
                    "Could not restore latest analysis:",
                    error
                );

            }

        }


        return analysis;

    }


    function setEvidenceLoading(
        loading
    ) {

        const button =
            $("checkEvidenceBtn");

        const loadingElement =
            $("evidenceLoading");


        if (button) {

            button.disabled =
                loading;


            button.innerHTML =

                loading

                    ? `
                        <span
                            class="spinner-border spinner-border-sm me-2">
                        </span>
                        Checking...
                      `

                    : `
                        <i class="bi bi-shield-check"></i>
                        Check Evidence
                      `;

        }


        if (loadingElement) {

            loadingElement.style.display =
                loading
                    ? "flex"
                    : "none";

        }

    }


    async function checkMissingEvidence() {

        const results =
            $("evidenceResults");


        if (!results) {
            return;
        }


        try {

            setEvidenceLoading(
                true
            );


            results.innerHTML =
                "";


            const analysis =
                await getAnalysisForEvidence();


            if (!analysis) {

                throw new Error(
                    "Please analyze the resume first."
                );

            }


            const resumeText =
                analysis.resume_text ||
                analysis.extracted_text ||
                window.resumeUploadData?.extracted_text ||
                "";


            const jdText =
                analysis.job_description ||
                analysis.jd_text ||
                jobDescription?.value ||
                "";


            const missingSkills =
                Array.isArray(
                    analysis.missing_skills
                )
                    ? analysis.missing_skills
                    : [];


            if (!resumeText) {

                throw new Error(
                    "Resume text is not available. Please upload the resume again."
                );

            }


            if (!jdText) {

                throw new Error(
                    "Job description is not available."
                );

            }


            if (!missingSkills.length) {

                results.innerHTML = `

                    <div class="evidence-empty">

                        <i class="bi bi-check-circle-fill"></i>

                        <h5>
                            No Missing Skills
                        </h5>

                        <p>
                            No missing job skills were detected.
                        </p>

                    </div>

                `;

                return;

            }



            const response =
                await fetch(
                    "/analysis/evidence-check",
                    {
                        method: "POST",

                        credentials:
                            "same-origin",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            resume_text:
                                resumeText,

                            job_description:
                                jdText,

                            missing_skills:
                                missingSkills

                        })

                    }
                );


            const data =
                await response.json();


            if (
                !response.ok ||
                !data.success
            ) {

                throw new Error(
                    data.message ||
                    "Evidence analysis failed."
                );

            }


            renderEvidenceResults(
                data.evidence || []
            );


        } catch (error) {

            console.error(
                "Evidence error:",
                error
            );


            results.innerHTML = `

                <div class="alert alert-danger">

                    <i class="bi bi-exclamation-triangle me-2"></i>

                    ${escapeHtml(
                        error.message
                    )}

                </div>

            `;

        } finally {

            setEvidenceLoading(
                false
            );

        }

    }



    function renderEvidenceResults(
        evidence
    ) {

        const results =
            $("evidenceResults");


        if (!results) {
            return;
        }


        if (!Array.isArray(evidence) ||
            !evidence.length
        ) {

            results.innerHTML = `

                <div class="evidence-empty">

                    <i class="bi bi-check-circle-fill"></i>

                    <h5>
                        Everything looks good
                    </h5>

                    <p>
                        No additional evidence issues were detected.
                    </p>

                </div>

            `;

            return;

        }


        results.innerHTML =
            evidence.map(
                item => {

                    const status =
                        String(
                            item.status ||
                            "missing"
                        ).toLowerCase();


                    const confidence =
                        Math.max(
                            0,
                            Math.min(
                                100,
                                Math.round(
                                    Number(
                                        item.confidence ||
                                        0
                                    ) * 100
                                )
                            )
                        );


                    let icon =
                        "bi-question-circle";


                    let statusText =
                        "Needs Review";


                    if (
                        status === "missing"
                    ) {

                        icon =
                            "bi-exclamation-circle";

                        statusText =
                            "Missing";

                    } else if (
                        status === "indirect"
                    ) {

                        icon =
                            "bi-dash-circle";

                        statusText =
                            "Indirect Evidence";

                    } else if (
                        status === "supported"
                    ) {

                        icon =
                            "bi-check-circle";

                        statusText =
                            "Supported";

                    }


                    return `

                        <article
                            class="evidence-card"
                        >

                            <div
                                class="evidence-card-top"
                            >

                                <div>

                                    <h5>
                                        ${escapeHtml(
                                            item.skill ||
                                            "Unknown Skill"
                                        )}
                                    </h5>

                                    <span
                                        class="evidence-status status-${escapeHtml(status)}"
                                    >

                                        <i
                                            class="bi ${icon}">
                                        </i>

                                        ${statusText}

                                    </span>

                                </div>


                                <div
                                    class="evidence-confidence"
                                >
                                    ${confidence}%
                                </div>

                            </div>


                            <div
                                class="evidence-body"
                            >

                                <div
                                    class="evidence-detail"
                                >

                                    <strong>
                                        Evidence found
                                    </strong>

                                    <p>
                                        ${
                                            item.evidence
                                                ? escapeHtml(
                                                    item.evidence
                                                )
                                                : "No clear evidence was found."
                                        }
                                    </p>

                                </div>


                                <div
                                    class="evidence-recommendation"
                                >

                                    <i
                                        class="bi bi-lightbulb">
                                    </i>

                                    <div>

                                        <strong>
                                            Recommendation
                                        </strong>

                                        <p>
                                            ${escapeHtml(
                                                item.recommendation ||
                                                "Verify this skill before adding it."
                                            )}
                                        </p>

                                    </div>

                                </div>

                            </div>

                        </article>

                    `;

                }
            ).join("");

    }



    function initEvidenceStudio() {

        const button =
            $("checkEvidenceBtn");


        if (!button) {
            return;
        }


        button.addEventListener(
            "click",
            checkMissingEvidence
        );

    }



    /* =========================================================
       JOB RECOMMENDATIONS
       IMPORTANT:
       ONLY USE THE BACKEND API
    ========================================================= */

    async function loadRecommendedJobs() {

        const loading =
            $("recommendedJobsLoading");

        const empty =
            $("recommendedJobsEmpty");

        const grid =
            $("recommendedJobsGrid");


        if (
            !loading ||
            !empty ||
            !grid
        ) {

            console.warn(
                "Recommended Jobs UI elements not found."
            );

            return;

        }


        loading.style.display =
            "flex";

        empty.style.display =
            "none";

        grid.innerHTML =
            "";



        try {

            const response =
                await fetch(
                    "/jobs/recommended",
                    {
                        method: "GET",

                        credentials:
                            "same-origin",

                        headers: {
                            "Accept":
                                "application/json"
                        }
                    }
                );


            const data =
                await response.json();


            if (
                response.status === 401
            ) {

                window.location.href =
                    "/login";

                return;

            }


            if (
                response.status === 404
            ) {

                loading.style.display =
                    "none";

                empty.style.display =
                    "block";

                empty.innerHTML = `

                    <div class="empty-icon">
                        📄
                    </div>

                    <h3>
                        Upload your resume first
                    </h3>

                    <p>
                        Upload and analyze your resume to receive personalized job recommendations.
                    </p>

                `;

                return;

            }


            if (
                !response.ok ||
                !data.success
            ) {

                throw new Error(
                    data.message ||
                    "Unable to load recommended jobs."
                );

            }


            const jobs =
                Array.isArray(
                    data.jobs
                )
                    ? data.jobs
                    : [];


            if (!jobs.length) {

                loading.style.display =
                    "none";

                empty.style.display =
                    "block";

                return;

            }


            grid.innerHTML =
                jobs.map(
                    createBackendJobCard
                ).join("");


            loading.style.display =
                "none";

            empty.style.display =
                "none";


            /*
            Optional profile skills display
            */

            if (
                Array.isArray(
                    data.resume_skills
                )
            ) {

                renderRecommendedSkillSummary(
                    data.resume_skills
                );

            }

        } catch (error) {

            console.error(
                "Recommended jobs error:",
                error
            );


            loading.style.display =
                "none";

            empty.style.display =
                "block";


            empty.innerHTML = `

                <div class="empty-icon">
                    ⚠️
                </div>

                <h3>
                    Unable to load recommendations
                </h3>

                <p>
                    ${escapeHtml(
                        error.message ||
                        "Please try again."
                    )}
                </p>

                <button
                    type="button"
                    class="refresh-jobs-btn"
                    onclick="loadRecommendedJobs()"
                >
                    ↻ Try Again
                </button>

            `;

        }

    }



    function createBackendJobCard(
        job,
        index
    ) {

        const skills =
            Array.isArray(
                job.skills
            )
                ? job.skills
                : [];


        const matchedSkills =
            Array.isArray(
                job.matched_skills
            )
                ? job.matched_skills
                : [];


        const score =
            Number(
                job.match_score || 0
            );


        const skillHTML =
            skills
                .slice(0, 6)
                .map(
                    skill => `

                        <span class="job-skill">
                            ${escapeHtml(skill)}
                        </span>

                    `
                )
                .join("");


        const matchedHTML =
            matchedSkills
                .slice(0, 6)
                .map(
                    skill => `

                        <span class="matched-job-skill">

                            <i
                                class="bi bi-check-circle-fill">
                            </i>

                            ${escapeHtml(skill)}

                        </span>

                    `
                )
                .join("");


        const safeUrl =
            typeof job.url === "string"
                ? job.url
                : "";


        return `

            <article
                class="job-card"
                style="
                    animation-delay:
                    ${index * 80}ms;
                "
            >

                <div class="job-card-top">

                    <div class="job-icon">
                        💼
                    </div>


                    <div
                        class="job-match"
                    >
                        ${score}% Match
                    </div>

                </div>


                <h3>
                    ${escapeHtml(
                        job.title ||
                        "Job Opportunity"
                    )}
                </h3>


                <div
                    class="job-company"
                >
                    ${escapeHtml(
                        job.company ||
                        "Company"
                    )}
                </div>


                <div class="job-meta">

                    <span>

                        <i
                            class="bi bi-geo-alt">
                        </i>

                        ${escapeHtml(
                            job.location ||
                            "India"
                        )}

                    </span>


                    <span>

                        <i
                            class="bi bi-briefcase">
                        </i>

                        ${escapeHtml(
                            job.experience ||
                            "0-2 Years"
                        )}

                    </span>

                </div>


                ${
                    matchedHTML
                        ? `

                            <div
                                class="job-matched"
                            >

                                <small>
                                    Your matched skills
                                </small>

                                <div
                                    class="matched-skills"
                                >
                                    ${matchedHTML}
                                </div>

                            </div>

                          `
                        : ""
                }


                <div class="job-skills">

                    ${skillHTML}

                </div>


                <div
                    class="job-card-actions"
                >

                    <button
                        type="button"
                        class="view-job-btn"
                        data-job-url="${escapeHtml(
                            safeUrl
                        )}"
                    >

                        <i
                            class="bi bi-search">
                        </i>

                        Find Jobs

                    </button>


                    <button
                        type="button"
                        class="job-analyze-btn"
                        onclick="scrollToATS()"
                    >

                        <i
                            class="bi bi-file-earmark-text">
                        </i>

                        Analyze

                    </button>

                </div>

            </article>

        `;

    }



    /* =========================================================
       JOB BUTTON EVENTS
    ========================================================= */

    document.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    ".view-job-btn"
                );


            if (!button) {
                return;
            }


            const url =
                button.dataset.jobUrl;


            if (!url) {

                showToast(
                    "Job search link is unavailable.",
                    "danger"
                );

                return;

            }


            openJob(url);

        }
    );



    function openJob(url) {

        if (!url) {
            return;
        }


        window.open(
            url,
            "_blank",
            "noopener,noreferrer"
        );

    }


    window.openJob =
        openJob;



    /* =========================================================
       FIND JOBS
    ========================================================= */

    function findJobs(
        jobTitle
    ) {

        if (!jobTitle) {
            return;
        }


        const query =
            encodeURIComponent(
                `${jobTitle} jobs India`
            );


        const url =
            `https://www.linkedin.com/jobs/search/?keywords=${query}`;


        openJob(url);

    }


    window.findJobs =
        findJobs;



    /* =========================================================
       SCROLL TO ATS
    ========================================================= */

    function scrollToATS() {

        const target =
            $("atsResultsSection") ||
            $("atsAnalysis");


        if (target) {

            target.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

            return;

        }


        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });

    }


    window.scrollToATS =
        scrollToATS;



    /* =========================================================
       PROFILE SKILLS
    ========================================================= */

    function renderRecommendedSkillSummary(
        skills
    ) {

        const element =
            $("recommendedResumeSkills");


        if (!element) {
            return;
        }


        if (
            !Array.isArray(skills) ||
            !skills.length
        ) {

            element.innerHTML =
                "";

            return;

        }


        element.innerHTML =
            skills
                .slice(0, 12)
                .map(
                    skill => `

                        <span
                            class="profile-skill"
                        >
                            ${escapeHtml(skill)}
                        </span>

                    `
                )
                .join("");

    }



    /* =========================================================
       REFRESH JOB BUTTON
    ========================================================= */

    window.loadRecommendedJobs =
        loadRecommendedJobs;



    /* =========================================================
       INITIALIZATION
    ========================================================= */

    async function initializeDashboard() {

        console.log(
            "ResumeAI dashboard initializing..."
        );


        initEvidenceStudio();


        /*
        Load old data first.
        */

        await Promise.allSettled([

            loadHistory(),

            loadLatest()

        ]);


        /*
        Then load jobs.

        If there is no resume,
        backend returns a clear empty state.
        */

        await loadRecommendedJobs();


        console.log(
            "ResumeAI dashboard loaded successfully."
        );

    }


    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initializeDashboard
        );

    } else {

        initializeDashboard();

    }


})();
function updateATSCircle(score) {
    const circle = document.getElementById("atsResultCircle");
    const scoreElement = document.getElementById("atsResultScore");

    if (!circle || !scoreElement) {
        console.error("ATS circle elements not found");
        return;
    }

    let value = Number(score);

    if (!Number.isFinite(value)) {
        value = 0;
    }

    value = Math.max(0, Math.min(100, value));

    scoreElement.textContent = Math.round(value);

    circle.style.setProperty("--ats-progress", `${value}%`);
}