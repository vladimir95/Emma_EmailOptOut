# EMMA SCRIPT FOR OPTING OUT INVALID EMAILS FROM EMMA. PLEASE READ THE "README" FILE FOR DETAILS
# @author: Vladimir Martintsov
# @email: vladimirmartintsov95@gmail.com


from emma import enumerations
from emma import exceptions as ex
from emma.model.account import Account
from pprint import pprint
from datetime import datetime, timedelta
import csv, sys, os, time


#YOUR AUTHENTICATION INFO HERE (Account ID, public key, private key)
emma_account = Account(1234, "abcd1234", "abcd1234")

#Total, erroneous, opted-out, and active emails count
total_emails_count = 0
invalid_emails_count = 0
already_opted_out_emails_count = 0
opted_out_emails_count = 0
active_emails_count = 0



current_time=time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())
output_csv_name= "Invalid_Emma_emails_" + current_time + ".csv"
three_months_period_date_check = datetime.now() - timedelta(days=90)



#Local email address sanity check for correctness before calling API
# all the other special characters will have to be verified through Emma

#TWO CONDITIONS:
# if there are commas and spaces present - email is invalid
# if there are less or more than one @ - the email is invalid
#Otherwise - valid and to be checked in Emma
def email_invaild(email):
  at_symbol_count = email.count("@")

  if " " not in email and "," not in email and at_symbol_count == 1:
    return False
  else:
    return True


def main():
  global invalid_emails_count
  global total_emails_count
  global current_time
  global output_csv_name
  global emma_account
  global already_opted_out_emails_count
  global three_months_period_date_check
  global opted_out_emails_count
  global active_emails_count


  # STEP 0: OPEN THE CSV WITH ALL ERRORS EXPORTED FROM EMMA AND OPEN THE OUTPUT FILE FOR THE RESULTS
  
  with open(sys.argv[1], "r", encoding="ISO-8859-1") as emma_errors_csv_list:
    if not (emma_errors_csv_list.name.lower().endswith('.csv')):
      print("The file you are trying to work with is not in CSV format. Please save it in CSV format and try running the script again.")
      sys.exit(0)
    main_list_reader = csv.reader(emma_errors_csv_list, delimiter=",")
    next(main_list_reader)


    #INTRODUCTORY MESSAGE WITH SOME INFO

    time.sleep(3)
    print("-------------------------------------------------------------------------------------")
    print("Emma email script: opting out all the emails that have never received an email in 90 days or longer back from now.\n")
    print("Accounts that were sent an email within the 90 days timeframe will be kept as active!")
    time.sleep(10)
    print("-------------------------------------------------------------------------------------")
    print("Reminder: the 90 days from today's date is: " + str(three_months_period_date_check.strftime("%B %d, %Y")) + 
      ".\nAll the inactive accounts will be opted-out as part of this script.")
    time.sleep(10)
    print("-------------------------------------------------------------------------------------")
    print("BEGIN EXECUTING SCRIPT. PLEASE DO NOT TURN OFF YOUR MACHINE AND ENSURE STABLE INTERNET CONNECTION.")
    print("-------------------------------------------------------------------------------------")
    time.sleep(10)
    with open(output_csv_name, "a+", newline='') as wrong_emails_file:
      columnnames = ['Email', 'Comment', 'Opted-out?']
      writer = csv.DictWriter(wrong_emails_file, fieldnames=columnnames)
      # Write the column names in output CSV
      writer.writeheader()


      for csv_row in main_list_reader:
        total_emails_count+=1

        # Say email column is column 0 in input CSV. 

        user_email = csv_row[0]

        delivered_email_flag = False

        response_400_flag = False

        print("Processed emails: "+ str(total_emails_count))


        #STEP 1: CHECK IF THE EMAIL IS INVALID
        # Check if the email is invalid. If yes, then put a relevant comment in output CSV and move to next email record.
        if email_invaild(user_email):
          try:
            invalid_emails_count+=1
            writer.writerow({'Email': user_email, 'Comment': 'Error: Invalid email' })
          # Should never happen, but just in case.    
          except PermissionError: 
            print("You have the Wrong_Emma_emails.csv CURRENTLY OPEN and this script cannot write to it. \n" 
              + "Please close the Excel Window and running this script again!")
            sys.exit(0)
          continue


        # STEP2: RETRIEVE THE USER EMAIL AND HANDLE ALREADY OPTED OUT MEMBERS OR NON-EXISTING IN EMMA MEMBERS.

        # Try the API request to retrieve member info.
        # If it fails due to 503 or other server errors, wait for 5 seconds and retry the request. Try this for 5 times.
        # If it fails due to 400 error - then the email does not exist in Emma. Record the error in output CSV and move to the next record.
        for attempt in range(5):
          try: 
            member_info = emma_account.members[user_email]
          except (ex.ApiRequest400, KeyError):
            invalid_emails_count+=1
            writer.writerow({'Email': user_email, 'Comment': 'Error: This email does not exist in Emma' })  
            response_400_flag = True
            #print('Error: This email does not exist in Emma')
            break
          except ex.ApiRequestFailed:
            print("Authentication error: Emma's server is returning HTTP 401 error due to authentication issues with your API key.\n")
            print("Please verify your API key and try re-running this script again.\n")
            sys.exit(0)
          except: 
            print("Retrieving member info: Emma's server is having some response issues. Will retry for 5 times, otherwise, the script will stop executing.\n")
            print("The script will wait for 5 seconds between each retry. \n")
            print("If successful, the script will move on to next record.\n")
            time.sleep(5) 
          else:
            # the request went through successfully, we are good to go.
            break
        else:
          print("Retrieving member info: Emma's server failed to respond, something is wrong on Emma's end. Make sure Emma's server is "+
           "running or retry running the script later.\n")  
          print("The script has finished executing. All the emails processed up until now are in the relevant Invalid_Emma_emails.csv. \n") 
          sys.exit(0)

        if response_400_flag:
          continue

        # Should not happen, but just in case
        if member_info is None:
          invalid_emails_count+=1
          writer.writerow({'Email': user_email, 'Comment': 'Error: This email does not exist in Emma' })
          #print('Error: This email does not exist in Emma')
          continue

        #if the member has been opted-out already, then we cannot opt them in again anyways, due to Emma's policies
        # so we report them as opted out already
        if member_info['member_status_id'] == 'o':
          already_opted_out_emails_count+=1
          writer.writerow({'Email': user_email, 'Comment': 'Warning: This email exists in Emma, but has already been opted-out!' , 'Opted-out?': "Y"})
          #print("Warning: This email exists in Emma, but has already been opted-out!")
          continue


        # STEP 3: RETRIEVE THE MAILINGS SENT TO THIS USER. IF 0 MAILINGS ARE SENT, FLAG THE USER. 
        # KEEP THE USER ACTIVE IFF: THERE IS AT LEAST ONE DELIVERED MESSAGE OR THE FIRST EMAIL WAS SENT WITHIN 3 MONTHS


        # Try the API request to retrieve member's mailings.
        # If it fails due to 503 or other server errors, wait for 5 seconds and retry the request. Try this for 5 times.
        for attempt in range(5):
          try:
            member_mailings = member_info.mailings.fetch_all()

          # Should not happen at this point but still 
          except ex.ApiRequestFailed:
            print("Authentication error: Emma's server is returning HTTP 401 error due to authentication issues with your API key.\n")
            print("Please verify your API key and try re-running this script again.\n")
            sys.exit(0)
          except: 
            print("Retrieving member's mailings: Emma's server is having some response issues. Will retry for 5 times, otherwise, the script will stop executing.\n")
            print("The script will wait for 5 seconds between each retry. \n")
            print("If successful, the script will move on to next record.\n")
            time.sleep(5)
          else:
            # the request went through successfully, we are good to go.
            break 
        else:
          print("Retrieving member's mailings: Emma's server failed to respond, something is wrong on Emma's end. Make sure Emma's server is "+
           "running or retry running the script later.\n")  
          print("The script has finished executing. All the emails processed up until now are in the relevant Invalid_Emma_emails.csv. \n") 
          sys.exit(0)

        if len(member_mailings) == 0:
          invalid_emails_count+=1
          writer.writerow({'Email': user_email, 'Comment': 'Error: This email exists in Emma, but has NO mailings!' })
          #print('Error: This email exists in Emma, but has NO mailings!')
          continue


        first_mailing_id = list(sorted(member_mailings))[0]
        first_mailing_date = member_mailings[first_mailing_id]['delivery_ts']

        #if the first mailing appears to be within the three months, then we keep the member Active whatsoever
        if (first_mailing_date > three_months_period_date_check): 
          writer.writerow({'Email': user_email, 'Comment': 'Active: Timestamp: The first email on this account is less than three months' ,
              'Opted-out?': "N"})
          #print('Active: Timestamp: the first email on this account is less than three months')
          continue

        for mailing_id in member_mailings.keys():
          # if there is at least ONE delivered message, then we keep the member Active whatsoever
          if (member_mailings[mailing_id]['delivery_type']) == 'd':
            writer.writerow({'Email': user_email, 'Comment': 'Active: This email has at least ONE delivered email', 'Opted-out?': "N" })
            #print('Active: this account has at least ONE delivered email')
            active_emails_count+=1
            delivered_email_flag = True
            break

        # If we have at least one email that was delivered for this account, then we have to move on to next record
        if delivered_email_flag:
          continue  

        # All the checks for the account to be Active have been passed. Accounts that made this far have to be opted-out.

        # Try the API request to opt out the member.
        # If it fails due to 503 or other server errors, wait for 5 seconds and retry the request. Try this for 5 times.
        for attempt in range(5):
          try:
            member_info.opt_out()
          except ex.ApiRequestFailed:
            print("Authentication error: Emma's server is returning HTTP 401 error due to authentication issues with your API key.\n")
            print("Please verify your API key and try re-running this script again.\n")
            sys.exit(0) 
          except: 
            print("Opting out a member: Emma's server is having some response issues. Will retry for 5 times, otherwise, the script will stop executing.\n")
            print("The script will wait for 5 seconds between each retry. \n")
            print("If successful, the script will move on to next record.\n")
            time.sleep(5)
          else:
            # the request went through successfully, we are good to go.
            break 
        else:
          print("Opting out a member: Emma's server failed to respond, something is wrong on Emma's end. Make sure Emma's server is "+
           "running or retry running the script later.\n")  
          print("The script has finished executing. All the emails processed up until now are in the relevant Invalid_Emma_emails.csv. \n") 
          sys.exit(0)

        writer.writerow({'Email': user_email, 'Comment': 'Opted-out: This email has NO delivered emails and hence opted-out', 'Opted-out?': "Y" })
        #print('Opted-out: this account has been opted-out')
        opted_out_emails_count+=1

      # Close the input and output CSV file
      wrong_emails_file.close()
    emma_errors_csv_list.close()  
  if(total_emails_count<1):
    print("Empty input CSV: The CSV from Emma is missing email entries. Make sure that the CSV exported from Emma has at least one email in it.") 
  elif(total_emails_count>=1):
    print("\n")
    print("*************************************************************")
    print("The Script has ended executing.\n")
    print("*************************************************************")
    print("There was found " + str(invalid_emails_count)+" invalid emails out of total "+str(total_emails_count)+ 
    " emails processed in this CSV and Emma.\n")  
    print("There has been: \n" 
      + " - "+ str(opted_out_emails_count) +"/"+str(total_emails_count) + " active emails opted out \n" 
      + " - "+ str(already_opted_out_emails_count) +"/"+str(total_emails_count) + " emails found that were already opted-out, and \n" 
      + " - "+ str(active_emails_count)+"/"+str(total_emails_count) + " remained as active.\n" )
    print("The overall results have been exported into " + str(output_csv_name)+ ".\n")

if __name__ == '__main__':
  main()
