$(document).ready(function () {
    $(".new_comment").hide();
    $(".reply").click(function (e) {
        e.preventDefault();
        var postId = $(this).attr("id").replace("reply_", "");
        var form = $("#new_comment_" + postId);

        if (form.is(":visible")) {
            form.hide();
        } else {
            form.show();
        }
    });
});

function submitComment(event, postId) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    fetch("/slcomment", {
        method: "POST",
        body: formData,
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                addCommentToDOM(postId, data.author, data.comment);
                form.style.display = "none";
                document.getElementById(`reply_${postId}`).style.display =
                    "block";

                // Switch the default commenter
                const authorSelect = form.querySelector(
                    'select[name="author"]'
                );
                const currentAuthor = authorSelect.value;
                const newAuthor =
                    currentAuthor === "family" ? "raza" : "family";
                authorSelect.value = newAuthor;

                // Update the form's default value
                authorSelect.querySelector(
                    `option[value="${newAuthor}"]`
                ).selected = true;

                // Clear the textarea
                form.querySelector('textarea[name="comment"]').value = "";

                console.log("Current author before switch:", currentAuthor);
                console.log("New author after switch:", newAuthor);
                console.log("Select value after update:", authorSelect.value);
            } else {
                alert("Error submitting comment. Please try again.");
            }
        })
        .catch((error) => {
            console.error("Error:", error);
            alert("An error occurred. Please try again.");
        });

    return false;
}

function addCommentToDOM(postId, author, comment) {
    const commentContainer = document.querySelector(
        `#new_comment_${postId}`
    ).previousElementSibling;

    // Create a new paragraph for the comment
    const newComment = document.createElement("p");
    newComment.classList.add(
        "mb-2",
        "bg-yellow-100",
        "rounded",
        "transition-colors",
        "duration-500"
    );

    // Create the strong element for the author
    const authorElement = document.createElement("strong");
    authorElement.textContent = `${author}:`;

    // Append the author and comment text
    newComment.appendChild(authorElement);
    newComment.appendChild(document.createTextNode(` ${comment}`));

    // Insert the new comment before the comment container
    commentContainer.parentNode.insertBefore(newComment, commentContainer);

    // Remove highlight after 2 seconds
    setTimeout(() => {
        newComment.classList.remove("bg-yellow-100");
    }, 1000);
}
