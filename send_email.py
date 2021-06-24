import smtplib

sender_email = "asdfasdfa.52@gmail.com"
rec_email = "adfasdf.52@gmail.com"
password = input(str("Please enter your password : "))
#asdasdfadfadsf
message = "Hey, this was sent using python"

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(sender_email, password)
print("Login success")
server.sendmail(sender_email, rec_email, message)
print("Email has been sent to ", rec_email)
