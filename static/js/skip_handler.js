const inputField = document.querySelector("#genre_guess");
const submitButton = document.querySelector("input[type='submit']");

inputField.addEventListener("input", function() {
  if (inputField.value === "") {
    submitButton.value = "skip";
  } else {
    submitButton.value = "guess";
  }
});
