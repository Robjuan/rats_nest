RATS_NEST
Rob Andy Take Stats - Nearly Every Stat Taken

Eventually this will be:
* db_output - take csv in, make basic stats available
* rats_analysis - advanced analytics
* rats_nest - the backend / server etc that powers this

This is a web app done on Heroku, with Django as the framework.
PostgreSQL is our database.
PostgreSQL version must be 11.1+
> 11.0 has bug that affect us

Workflow:

## Active Development:
ensure running using 'local_development' settings, or custom
*** to ensure: 
set Environment Variable 'DJANGO_SETTINGS_MODULE' to 'rats_nest.settings.local_development'
on mac this is "export DJANGO_SETTINGS_MODULE rats_nest.settings.local_development'


Write code locally
run heroku local to test
Commit to working_dev branch of repo

## Remote Development:
**
** CHECK WITH PARTNER BEFORE DOING THIS - security leaks here will expose our database
**
Log in to Heroku > Deploy > Manual Deploy (at bottom)
Deploy the working_dev branch.
Roll back to master when done?


## Production Deployment:

Merge working_dev branch to master branch
-- git checkout master
-- git merge working_dev
Log in to Heroku > Deploy > Manual Deploy (at bottom)
Deploy the master branch.

