# Emma_EmailOptOut: Automatically opt out invalid emails from Emma email marketing platform using Python

These instructions are meant for all users and should help reducing the risk of using this script not as intended

Prepared by: Vladimir Martintsov

The script and this file are also available at github.com/vladimir95

Note: this Python script uses a Python Wrapper Emma API prepared by Doug Hurst; API code can be found here https://github.com/myemma/EmmaPython

Pre-story:
Emma (https://myemma.com/) - is an email marketing platform that allows to send massive email campaigns to hundreds of thousands subscribers. Both Emma and Emma's clients experience issues with having too many invalid emails that cause "Bounces" (emails not being delivered) as they are wrong or do not exists on the domain. This causes the bounce rates to go up and generates negative image for both marketing firms and Emma.  

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Installation and Running Instructions (Python 3.6.7)

- install Python 3.6.7 and pip on your machine
- install "requests" package for Python
- download the Python Emma Wrapper API from https://github.com/myemma/EmmaPython, and unzip it in a directory of your preference. You should see EmmaPython-master folder unzipped
- put Emma_OptOut_Script.py into EmmaPython-master directory. This will help with importing Emma's packages properly
- have your CSV with emails you want to check in EmmaPython-master directory as well
- have your API key ready (https://settings.e2ma.net/account/api-key) and modify the script - line 15 - as per your account's keys. If your Key is wrong, you will get Authentication Error.
- run Command Prompt in same directory and type "python Emma_OptOut_Script.py " followed by the name of your CSV file with emails (i.e: "Errors_List_from_Emma.csv")
- the example of exact command is then "python Emma_OptOut_Script.py Errors_List_from_Emma.csv"
- the script should run and generate the "Invalid_Emma_emails_timestamp.csv" file in the Same directory

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Requirements satisfied by the script:


### Requirement 1: This script WILL OPT OUT (in Emma's system) the users (and their emails) from all email campaigns in Emma that have (READ CAREFULLY):

- an email address of correct format, but it causes either a "hard" (Emma mailing status :"b") or a "soft"(Emma mailing status :"s") bounce FOR ALL MAILINGS sent to it during the past 4 months or longer. (Emma keeps the history of mailings sent to the user for 1.5 years and not longer). In other words, the email address that never received any of the mailings.

### Requirement 2: This script will NOT opt out (and will keep as Active in Emma's system) the users that have:
- a valid email address that have at least one mailing received for the past 1.5 years. 
- a valid email address and profile whose FIRST EMAIL was within the past 90 days FROM today's date - the new users that may still cause soft or hard bounce will NOT be opted out yet. 
- an email address and profile that has already been opted out and hence is not required to be opted out again

### Requirement 3: The script will report (locally in CSV and NOT in Emma's system) as Error the following emails:
- email address of wrong format in Emma (specifically: emails with two @'s, 1 or more spaces or commas in them) - Emma sets those profile to "Error" status after the campaign email has been sent
- a vaild email address that has NO mailings: either the user is too new or last email sent to user was more than 1.5 years ago
- an email that does not exist in Emma's database
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Input and Output Specifications:

Input: The script requires a CSV(not .xlsx or any other format!) with emails of your choice (usually, you can get them by exporting "Errors" in Emma and saving it as CSV). The script will skip the heading in CSV and move on to the second row for teh actual record.

**NOTE: The input CSV has to have email address in its first column!**

Output: A CSV file with three columns (Email, Comment, Opted-Out?), where:
- Email: the email from the original CSV in the same order 
- Comment: can be as:
	'Active: This email has at least ONE delivered email' - indicates that this email has at least one mailing delivered to it successfully
	'Active: Timestamp: The first email on this account is less than three months' - indicates a fresh account which first email has been sent out within the three months timeframe
	'Error: Invalid email' - indicates an erroneous email with either space(-s), comma(-s) or with 0 or 2 or more '@'s
	'Error: This email does not exist in Emma' - indicates that this email cannot be found in Emma
	'Error: This email exists in Emma, but has NO mailings!' - indicates that no mailings can be found on this account's record
	'Opted-out: This email has NO delivered emails and hence opted-out' - indicates that this email has been opted-out from Emma, as it has satisfied the Opt-Out Requirement 1
	'Warning: This email exists in Emma, but has already been opted-out!' - indicates that this email has already been opted out from Emma previously

- Opted-Out? can be as either Y or N depending if the email has been opted out or not.
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Things the Script takes care of the following exceptions and generate respective errors:

- Empty input CSV: in case if the input file is empty or has no entries, thsi error will appear. NOTE: Usually, when exporting emails from Emma, it generates a CSV with first row with headers(email, name, etc.).
The Script WILL skip this first row and move onto the next row for actual email entry. If there are no emails, then this error will appear.

- Authentication error: in case if API key is wrong, the respective message will appear.
- Retreiving info or Opting Out error: in case if Emma's server is too overloaded and becomes unresponsive to process the request, the script will attempt 4 more times to re-send the request
- Retreiving info or Opting Out failure: in case if Emma's server fails to respond for 5 times, then the script will stop executing and the processed emails will be saved in outputted CSV

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
