import json
import boto3 
import datetime
#import smtplib
#from email.MIMEMultipart import MIMEMultipart
#from email.MIMEText import MIMEText
#from email.MIMEBase import MIMEBase
#from email.mime.multipart import MIMEMultipart
#from email.mime.text import MIMEText
#from email.mime.base import MIMEBase
#from email import encoders
import time 
from jira import JIRA 
from jira.exceptions import JIRAError

ses_client = boto3.client('ses')
iam_client = boto3.client('iam')
secman_client = boto3.client('secretsmanager') 
sqs_client = boto3.client('sqs')


def pollqueue():
    sqs_client = boto3.client('sqs')
    for message in sqs_client.receive_message(QueueUrl="https://sqs.ap-south-1.amazonaws.com/*********/QueueEvent", MessageAttributeNames=['BodyData']):
        #if message.message_attributes is not None:
         #   Email_array = message.message_attributes.get('BodyData').get('StringValue').split
          #  print(Email_array)
            #sendmail2(Email_array[0], Email_array[1], Email_array[2], Email_array[3], Email_array[4])
        print(message)

def sendmail(source, d_to, d_cc, mes_sub, mes_body):
    try:
        mailresponse = ses_client.send_email(
            Source=source, 
            Destination={'ToAddresses':[d_to], 'CcAddresses':[d_cc]}, 
            Message={'Subject':{'Data':mes_sub}, 'Body':{'Text':{"Data": mes_body}}}
            )
        print(mailresponse)
    except ses_client.exceptions.MessageRejected:
        print("Message Rejected")
    except ses_client.exceptions.MailFromDomainNotVerifiedException:
        print("Domain Not Verified")
    else:
        print("Nothing")

def sendmail2(source, d_to, d_cc, mes_sub, mes_body):
    fromaddr = source   
    #toaddr = ", ".join(d_to)
    #ccaddr = ", ".join(d_cc)
    msg = MIMEMultipart()

    msg['From'] = fromaddr
    msg['To'] = d_to
    msg['CC'] = d_cc
    msg['Subject'] = mes_sub

    body = mes_body

    msg.attach(MIMEText(body, 'html'))
    print("inside send mail function")
    server = smtplib.SMTP('NSMAIL_SERVER.com')
    text = msg.as_string()
    server.sendmail(fromaddr, d_to, text)
    print("mail has been sent")
    server.quit()
            
            

def sendmail3(source, d_to, d_cc, mes_sub, mes_body):
    queue_url = "https://sqs.ap-south-1.amazonaws.com/**********/QueueEvent"
    
    response = sqs_client.send_message(
        QueueUrl=queue_url,
        DelaySeconds=5,
        MessageAttributes={
            'Title': {
                'DataType': 'String',
                'StringValue': 'Access key roation lambda'
            },
            'Author': {
                'DataType': 'String',
                'StringValue': 'Sagar Jangam'
            },
            'WeeksOn': {
                'DataType': 'Number',
                'StringValue': '6'
            }, 
            'BodyData': {
                'DataType': 'String',
                'StringValue': "{}+{}+{}+{}+{}".format(source, d_to, d_cc, mes_sub, mes_body) 
            }
        }, 
        MessageBody='This is the body of the message'
    )


users = {}

# A test function to quickly replicate the behaviour for sample users
def iamquery_test():
    userlist = iam_client.list_users() 
    for user in userlist['Users']:
        if(user['UserName'] == "User1" or user['UserName'] == "User2"):
            u_name = user['UserName']
            ### making a dict of users with keyid, createdate, and tag(stakeholder)
            user_access_key_1 = iam_client.list_access_keys(UserName=u_name)
            if(len(user_access_key_1['AccessKeyMetadata']) > 0):
                u_key = user_access_key_1['AccessKeyMetadata'][0]['AccessKeyId']
                u_key_age =  abs(user_access_key_1['AccessKeyMetadata'][0]['CreateDate'] - datetime.datetime.now(datetime.timezone.utc)).days
                u_mail = []
                u_tags = iam_client.list_user_tags(UserName = u_name)['Tags']
                for u_tag in u_tags:
                    if(u_tag['Key'].upper() == "LOB_HEAD" or u_tag['Key'].upper() == "STAKEHOLDER_2"): #Checking the existance of two stakeholders
                        u_mail.append(u_tag['Value'])
                    
                users[u_name] = [u_key, u_key_age, u_mail[0], u_mail[1]] ### add stakeholders email from the tags
            else: 
                users[u_name] = ['NoKeys', '0'] ### users with no keys, add email from tags
    #print user after the loop is done
    #print(users)        
    print("The Users have been queries, a sample user account: {}".format(users.keys()))
        

def iamquery():
    userlist = iam_client.list_users() 
    for user in userlist['Users']:
        u_name = user['UserName']
        ### making a dict of users with keyid, createdate, and tag(stakeholder)
        user_access_key_1 = iam_client.list_access_keys(UserName=u_name)
        if(len(user_access_key_1['AccessKeyMetadata']) > 0):
            u_key = user_access_key_1['AccessKeyMetadata'][0]['AccessKeyId']
            u_key_age =  abs(user_access_key_1['AccessKeyMetadata'][0]['CreateDate'] - datetime.datetime.now(datetime.timezone.utc)).days
            u_mail = []
            u_tags = iam_client.list_user_tags(UserName = u_name)['Tags']
            for u_tag in u_tags:
                if(u_tag['Key'].upper() == "LOB_Head" or u_tag['Key'].upper() == "StakeHolder2"):
                    u_mail.append(u_tag['Value'])
                #else(u_tag['Key'] == "Ticket"):
                    #u_ticket = u_tag['Value']
                    
            users[u_name] = [u_key, u_key_age, u_mail[0], u_mail[1]] u_ticket### add stakeholders email from the tags
        else: 
            users[u_name] = ['NoKeys', '0'] ### users with no keys, add email from tags
    print(users)
def auth_jira():
    jira_server = "http://jira_server.com"
    #we can instead pass these in the Lambda configuration
    jira_user = "JIRA_User" 
    jira_pass = "PASSWORD"
    
    options = {'server':jira_server}
    try:
        jira = JIRA(options, basic_auth=(jira_user, jira_pass))
        return "Authentication successfull"
    except JIRAError as e:
        if e.status_code == 401: 
            print("Authentication failed, check username and password. \nRun again.... ")
            sys.exit()
    
#generate jira ticket    
def gen_ticket(u_name):
    jira_server = "http://jira_server.com/"
    #we can instead pass these in the Lambda configuration
    jira_user = "JIRA_USER"
    jira_pass = "PASSWORD"
    
    options = {'server':jira_server}
    try:
        jira = JIRA(options, basic_auth=(jira_user, jira_pass))
        print("Authentication successfull")
    except JIRAError as e:
        if e.status_code == 401: 
            print("Authentication failed, check username and password. \nRun again.... ")
            sys.exit()
    #auth_status = auth_jira()
    #if (auth_status == "Authentication successfull"):
    issue_list = [
    {
    'project':'SOME_JIRA_PROJECT',
    'summary': 'A request from Lambda',
    'description': 'Creating this ticket for testing a lambda for automated access key roation',
    'issuetype': {"name":"task1", 'id':'3'},
    #'customfield_10300': {'value':'GIT'},
    'components': [{'name': 'Test'}]
    }
    ]
    if (len(issue_list) > 1):
    # modify the code to write the separate issue numbers
        try: 
            issue = jira.create_issues(field_list=issue_list)
            #print("issue created {} ".format(issue))
            return issue  
        except JIRAError as e: 
            print(e.message)
            return "error in generating ticket"
    else: 
        try:
            issue = jira.create_issue(fields=issue_list[0])
                #print("issue created {}".format(issue))
            return issue
        except JIRAError as e:
            print(e)
            return "error in generating ticket"
    

def query_ticket(u_name):
    auth_status = auth_jira()
    if(auth_status == "Authentication successfull"):
        ticket_id = users[u_name][4]
        #issue_status = jira.
    
    

#save the key in secrets manager    
def save_key(u_name, u_key, u_secret):
    unique_name = "accessKey_rotation_"
    unique_name = unique_name + u_name
    secman_client.create_secret(Name=unique_name, SecretString=u_secret) # change the code to keep the path constant
    print("Key had been created and added to the Secret Manager: " +unique_name +"for user: " + "u_name")


#delete the entry from sec manager 
def del_sec(u_name, u_key):
    unique_name = "accessKey_rotation_"
    unique_name = unique_name + u_name
    secman_client.delete_secret(SecretId = unique_name, RecoveryWindowInDays=10) ## change the recovery window

#generate new key
def gen_key(u_name):
    temp_key = iam_client.create_access_key(UserName=u_name)
    # save the key to the secrets manager, add the key id as well, as json
    save_key(temp_key['AccessKey']['UserName'], temp_key['AccessKey']['AccessKeyId'], temp_key['AccessKey']['SecretAccessKey'])

#disable the existing key
def dis_key(u_name, u_key):
    iam_client.update_access_key(UserName = u_name, AccessKeyId = u_key, Status = 'Inactive')

# delete the old key 
def del_key(u_name, u_key):
    iam_client.delete_access_key(UserName = u_name, AccessKeyId = u_key)
    del_sec(u_name, u_key)


def check_key():
    for u_name in users:
        if (users[u_name][1] >= 75 and users[u_name][1] < 80):
            print("The user's: " + u_name +" key "+ users[u_name][0] + "is older than 75 days, thus sending email and generating ticket")
            sendmail2("mail1@domain.com", users[u_name][2], users[u_name][3], "An email reminder for AWS access key rotation", "Hi Update your keys")
            print(users[u_name][2])
    
        elif (users[u_name][1] >= 80  and users[u_name][1] < 90): 
            print("The user's: " + u_name +" key "+ users[u_name][0] + "is older than 80 days, thus generating new key and sending email")
            gen_key(u_name)
            #sendmail2("mail1@domain.com", users[u_name][2], users[u_name][3], "An email reminder for AWS access key rotation", "Hi Update your keys")
    
        elif (users[u_name][1] >= 90 and users[u_name][1] < 100):
            dis_key(u_name, users[u_name][0])
            #sendmail2(users[u_name][2], users[u_name][3], "stakeholder1@mail.com + stakehodler2@mail.com", "An email reminder for AWS access key rotation", "Hi Update your keys")
    
        elif (users[u_name][1] >= 100 and users[u_name][1] < 110):
            del_key(u_name, users[u_name][0])
        
        else:
            print("The key is older than 110 days thus")
            gen_key(u_name)
            sendmail2("stakeholder@mail.com", users[u_name][2], users[u_name][3], "This is a test mail", "This email is from lambda")
            #dis_key(u_name, users[u_name][0])
            #del_key(u_name, users[u_name][0])

# an initial fucntion to intimate the users with keys aged over 610 days, keep changin the day unitl you reach the makr of 75 days all keys are 
def sample_check():
    for u_name in users:
        if (int(users[u_name][1]) >= int(900)):
            print("The user's: " + u_name +" key "+ users[u_name][0] + "is older than 610 days, thus sending email and generating ticket")
            #sendmail3("soc@domain.com", "stakeholder1@mail.com", users[u_name][0], "Email from Lambda", "Hi this a test mail from Lambda")
            #print(users[u_name][2])
            # enable the gen key function after test runs
            #gen_key(u_name)
            ticket_id = gen_ticket(u_name)
            if(str(ticket_id) != "error in generating ticket"):
                iam_client.tag_user(UserName=u_name, Tags=[{'Key': 'Ticket_ID', 'Value': str(ticket_id)}])
                sendmail3("mail1@domain.com", users[u_name][2], users[u_name][3], "Automated access key rotation", "Hi, Kindly check the ticket generated for {} user account & {} and take respective action").format(u_name, users[u_name][0])

            else:
                sendmail3("mail1@domain.com", "stakeholder@mail.com", "stakeholder2@mail.com", "Error | Automated access key rotation", "There was an error in generating ticket for {}").format(u_name)

        if (int(users[u_name][1]) >= int(500)):
            print("The user's: " + u_name +" key "+ users[u_name][0] + "is older than 610 days, thus sending email and generating ticket")
            # enable the gen key function after test runs
            #gen_key(u_name)
            if(u_name == "some-user"):
                ticket_id = gen_ticket(u_name)
                if(str(ticket_id) != "error in generating ticket"):
                    iam_client.tag_user(UserName=u_name, Tags=[{'Key': 'Ticket_ID', 'Value': str(ticket_id)}])
                    gen_key(u_name)
                    sendmail3("mail1@domain.com", users[u_name][2], users[u_name][3], "Automated access key rotation", "Hi, Kindly check the ticket generated for {} user account & {} and take respective action").format(u_name, users[u_name][0])

                else:
                    sendmail3("mail1@domain.com", "stakeholder@mail.com", "stakeholder2@mail.com", "Error | Automated access key rotation", "There was an error in generating ticket for {}").format(u_name)



def lambda_handler(event, context):
    # TODO implement
    #print(time.perf_counter())
    #print(time.perf_counter())
    #iamquery_test() ## query for two test users only 
    iamquery()
    #print("starting sample check")
    sample_check()
    #print("doen with sample check")
    #iamquery() ## enable this post testing
    #print(time.perf_counter())
    #check_keˍ
    #print(time.perf_counter())
    
    #test code 
    print(users)
    #pollqueue()
    print("Entered!")

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from L!')
    }

