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
ensure running using 'local_development' settings, or custom
Write code locally
run heroku local to test
Commit to working_dev branch of repo

Deploy:
*** CHECK WITH PARTNER BEFORE DEPLOYING *** 

Merge working_dev branch to master branch
-- git checkout master
-- git merge working_dev
Log in to Heroku > Deploy > Manual Deploy (at bottom)
