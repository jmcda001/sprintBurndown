# sprintBurndown
Sprint burndown generator for Trello boards. Parses the JSON object of a Trello board used for Kanban or Scrum for a entrepreneurial project. Provides a CSV of the progress of User Stories and Biz/Dev tasks throughout all stages (Backlog, In Progress, In Review, Done) and calculates how many Small, Medium, Large tasks each member contributed to. Developed for Sprint burndowns of the groups in a Faculty Led Summer Study Abroad Program (FLEAP) through University of California, Riverside (UCR). Summer: 2019. Location: London.

# API Key/Token
Requires a `config.py` file with a `TRELLO_API_KEY` and `TRELLO_API_TOKEN` populated. 

# Usage
`python burndown.py -h` to view the command line options
`--url URL` Pass in the filename containing the URL of the Trello board
`-f FILENAME` Pass in the filename of the exported JSON file from the Trello board

# Output
.CSV file in the `csv/` directory.
Provides card counts in each "stage" (list) of development on its own row. Outputs each members contributions to the "Biz/Dev Done" list in terms of (Small, Medium, Large) tasks and the average number of team members on the tasks (cards) they were worked on. 

Optionally allows to list out each members contributions to various stages. As an optional parameter to `writeBurndown()` pass in the list of stages you want a member breakdown for as the `memberBreakdown` argument.
