document.addEventListener("DOMContentLoaded", () => {

    /*
     * SAVE DSA PROBLEM
     */

    document.querySelectorAll(".save-problem")
        .forEach(button => {

            button.addEventListener("click", async () => {

                const problemId =
                    button.dataset.problemId;

                try {

                    const response =
                        await fetch(
                            `/learning/dsa/${problemId}/save`,
                            {
                                method: "POST"
                            }
                        );

                    const data =
                        await response.json();

                    if (!data.success) {
                        return;
                    }

                    button.classList.toggle(
                        "saved",
                        data.saved
                    );

                } catch (error) {

                    console.error(
                        "Save error:",
                        error
                    );

                }

            });

        });


    /*
     * UPDATE STATUS
     */

    document.querySelectorAll(".status-select")
        .forEach(select => {

            select.addEventListener(
                "change",
                async () => {

                    const problemId =
                        select.dataset.problemId;

                    const status =
                        select.value;

                    const formData =
                        new FormData();

                    formData.append(
                        "status",
                        status
                    );

                    try {

                        const response =
                            await fetch(
                                `/learning/dsa/${problemId}/status`,
                                {
                                    method: "POST",
                                    body: formData
                                }
                            );

                        const data =
                            await response.json();

                        if (!data.success) {

                            alert(
                                data.message ||
                                "Unable to update progress."
                            );

                        }

                    } catch (error) {

                        console.error(
                            "Progress error:",
                            error
                        );

                    }

                }
            );

        });

});