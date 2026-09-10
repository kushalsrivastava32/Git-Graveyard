const repositoryPathInput = document.getElementById("repositoryPath");
const analyzeButton = document.getElementById("analyzeButton");
const status = document.getElementById("status");

const repositoryName = document.getElementById("repositoryName");
const repositoryBranch = document.getElementById("repositoryBranch");
const totalCommits = document.getElementById("totalCommits");
const totalContributors = document.getElementById("totalContributors");

const latestCommitMessage = document.getElementById("latestCommitMessage");
const latestCommitAuthor = document.getElementById("latestCommitAuthor");
const latestCommitDate = document.getElementById("latestCommitDate");


analyzeButton.addEventListener("click", analyzeRepository);


async function analyzeRepository() {

    const path = repositoryPathInput.value.trim();

    if (!path) {
        status.textContent = "Please enter a repository path.";
        return;
    }

    status.textContent = "Analyzing repository...";

    try {

        const response = await fetch(
            "http://127.0.0.1:5000/api/repository/analyze",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    path: path
                })
            }
        );


        const data = await response.json();


        if (!response.ok) {
            status.textContent = data.error || "Something went wrong.";
            return;
        }


        displayRepositoryData(data);

        status.textContent = "Repository analyzed successfully.";

    } catch (error) {

        console.error(error);

        status.textContent =
            "Could not connect to the backend.";
    }
}


function displayRepositoryData(data) {

    const repository = data.repository;
    const commits = data.commits;


    repositoryName.textContent = repository.name;
    repositoryBranch.textContent = repository.current_branch;

    totalCommits.textContent = commits.total_commits;

    totalContributors.textContent =
        commits.contributors.total_contributors;


    const latestCommit = commits.latest_commit;

    if (latestCommit) {

        latestCommitMessage.textContent =
            latestCommit.message;

        latestCommitAuthor.textContent =
            latestCommit.author_name;

        latestCommitDate.textContent =
            latestCommit.date;
    }
}