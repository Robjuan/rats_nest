RATS_NEST
Rob Andy Take Stats - Nearly Every Stat Taken

This platform will allow us to take in stats output by UltiAnalytics, and store them persistently, to enable taking longitudinal "career" stats.
Additionally, the database structure will allow us to more readily write advanced analysis packages and produce higher-order stats.

Heroku is our server/backend, Django is the framework, PostgreSQL is our database.
PostgreSQL version must be 11.1+
(recommend BigSQL on mac)





Workflow:

## Active Development:

local_development (or custom) settings to be used.
(requires env variable DJANGO_SETTINGS_MODULE = 'rats_nest.settings.local_development')
heroku cli is used to test locally. (heroku local)

Merge working_dev branch to master branch when major milestones are completed locally.

## Remote Development:

** CHECK WITH PARTNER BEFORE DOING THIS - security leaks here will expose our database
** need to build a database protection process (investigate heroku options)

Log in to Heroku > Deploy > Manual Deploy (at bottom)
Deploy the appropriate branch (typically master, not sure on best practice here)

## Production Deployment:

Merge working_dev branch to master branch
-- git checkout master
-- git merge working_dev
Log in to Heroku > Deploy > Manual Deploy (at bottom)
Deploy the master branch.

