SELECT 'CREATE DATABASE replacedbname' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'replacedbname')\gexec
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'replacerepluser') THEN
        CREATE USER replacerepluser WITH REPLICATION ENCRYPTED PASSWORD 'replacereplpassword'; 
    END IF; 

END $$;
ALTER USER replacepostgresuser WITH PASSWORD 'replacepostgrespassword';

\c replacedbname;
CREATE TABLE IF NOT EXISTS Emails(
    EmailID SERIAL PRIMARY KEY,
    Email VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS PhoneNumbers(
    PhoneNumberID SERIAL PRIMARY KEY,
    PhoneNumber VARCHAR(20) NOT NULL

);
INSERT INTO Emails(Email) VALUES('test@test.ru');
INSERT INTO Emails(Email) VALUES('kate@gmail.com');
INSERT INTO PhoneNumbers(PhoneNumber) VALUES('8926789032');
INSERT INTO PhoneNumbers(PhoneNumber) VALUES('+78956736523');
