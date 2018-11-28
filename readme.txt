RATS_NEST
Rob Andy Take Stats - Nearly Every Stat Taken

Eventually this will be:
* db_output - make basic stats available
* db_input - upload basic stats from UltiAnalytics ouput
* rats_analysis - advanced analytics
* the_nest - the database and server backend that powers all this

This will be a web app done on Heroku, with Django as the framework


Workflow:

Active Development:
Write code locally, test on local Heroku locall
Commit to working_dev branch of repo

Deploy:
*** CHECK WITH PARTNER BEFORE DEPLOYING *** 

Merge working_dev branch to master branch
-- git checkout master
-- git merge working_dev
Master branch will be automatically deployed to Heroku
