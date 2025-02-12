import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import autogen
import psycopg2
import dotenv
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES

app = Flask(__name__)
#used to overcome CORS Policy issues.
CORS(app)



dotenv.load_dotenv()
#Environment variables
OPENAIKEY = os.getenv('OPEN_AI_KEY')
DATABASE_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME')
DATABASE_PORT = os.getenv('DATABASE_PORT')
AES_KEY = os.getenv('AES_KEY')


#agents configuration
llm_config = {
    #Temerature determines the creativity of response
    "temperature": 0,
    #config list to pass agent model and api key variable
    "config_list": [{"model": 'gpt-4o', 'api_key': OPENAIKEY}],
    #Currently set to none - will configure according after testing
    "timeout": None,
}

user_proxy = autogen.UserProxyAgent(
    #give user proxy a name
    name="User_proxy",
    # execution parameter to be passed to proxy
    code_execution_config={
        # only take the last number messages of conversation
        # "last_n_messages": 2,
        # directory to execute scripts and save files to.
        "work_dir": "groupchat",
        #setting if docker is in use to false
        "use_docker": False,
    },
    #Currently never taking user input after first input
    human_input_mode="NEVER",
    # Max number of auto replies before terminating conversation.
    max_consecutive_auto_reply=2,
)

# Currently the Agents have minimal configuration to troublshoot user proxy incorrectly functioning.
agent_one = autogen.AssistantAgent(
    name="MultiTalentAgent",
    #system_message= "First word in every response 'Writer: '",
    llm_config=llm_config,
)


#method to connect to the database
def connect_to_database():
    #pass database name, hostname, username
    #Connect to database using loaded environment variables
    conn = psycopg2.connect(database=DATABASE_NAME,
                            host=DATABASE_HOST,
                            user=DATABASE_USERNAME,
                            password=DATABASE_PASSWORD,
                            port=DATABASE_PORT)
    #return the connection
    return conn

# GET request endpoint - method to return a full chat previously had with an agent or agent team.
@app.route('/get_previous_chat', methods=['POST'])
def get_previous_chat():
    try:
        data = request.json
        chatName = data.get('chatName')
        if isinstance(chatName, str):
            
            #database connection made by calling connect_to _database method
            conn = connect_to_database()
            #cursor object to make connection and execute quesries
            cursor = conn.cursor()
            #select chat required
            query = "SELECT chatcontent FROM chattable WHERE chatname = %s"
            # Provide parameters as a tuple
            cursor.execute(query, (chatName,))  
            #fetchone used to grab single row
            result = cursor.fetchone()
            print(result)
            #chech result is valid and set the chat content
            if result:
                chat_content = result[0]
            else:
                #html content to have a nice display to the use, possible refactoring could be required.
                chat_content = "<div id = 'previous_chat_error'><h1 id= 'returned_data'> Error fetching chat data</h1><br /><h3 id = 'previous_chat_error_sub'> Please try again later</h3></div>"  
            #close the surson and connection.
            cursor.close()
            conn.close()
        
            
        #return the chat content.
        return jsonify({"message": chat_content}), 200
    except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
    
# GET request endpoint - method to return chat names
@app.route('/gather_previous_chat_names', methods=['POST'])
def gather_previous_chat_names():
    try:
        #extract data
        data = request.json
        email = data["email"]
        #database connection made by calling connect_to _database method
        conn = connect_to_database()
        #cursor object to make connection and execute quesries
        cursor = conn.cursor()
        #select chatname required 
        query = "select chatname from chattable where useremail = %s"
        cursor.execute(query, (email,))  # Provide parameters as a tuple
        #fetchone used to grab single row - only one chatname is required.
        result = cursor.fetchall()
        print(result)
        
        #close the surson and connection.
        cursor.close()
        conn.close()
        #return the result to the front end
        return jsonify({"message": result}), 200
    except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        #if an error occurs return the error
        return jsonify({"error": str(e)}), 500    
    
#POST endpoint to create an agent
@app.route('/create_agent', methods=['POST'])
def create_agencreate_agent():
    try:
        # Retrieve JSON data from the body
        data = request.json
        #email to determine which account the agent configuration belongs to.
        email = data["email"]
        #agents specialisation
        specialisation = data.get('specialisation')
        #promp to be used to configure agent
        prompt = data.get('prompt')  
        #database connection made by calling connect_to _database method
        conn = connect_to_database()
        #cursor object to make connection and execute quesries
        cursor = conn.cursor()
        #insert statement
        cursor.execute("INSERT INTO agentdata (useremail, agentspecialisation, agentconfig, temperature, userintervention) VALUES (%s, %s, %s, %s, %s)",
            (email, specialisation, prompt, 0.0, False))
        #commit the transaction
        conn.commit()
        #close cursor and connection.
        cursor.close()
        conn.close()
        # message to be alerted to the user
        result = "Agent Created"
        return jsonify({"message": result}), 200
    except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500    

#code to ensure agents name provided by user does not break naming standards of agent.
#https://www.geeksforgeeks.org/python-removing-unwanted-characters-from-string/?utm_source    
def refactor_agent_name(name):
    # Replace invalid characters with underscores
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)


#POST method to sign in user
#Method is currently unsused but was in use before implementing Auth0 athentication for the user sign in.  
@app.route('/sign_in_user', methods=['POST'])
def sign_in_user():
    try:
        # Retrieve JSON data from the body
        data = request.json
        
        userEmail = data["emailAddress"]
        userPassword = data["password"]  
        
        # Database connection
        conn = connect_to_database()
        cursor = conn.cursor()

        # Using parameterised query for SQL injection
        query = "SELECT useremail, userpassword FROM usertable WHERE useremail = %s"
        cursor.execute(query, (userEmail,))  # Provide parameters as a tuple

        # Fetch one result - result will be a tuple
        result = cursor.fetchone()
        #close the connection
        cursor.close()
        conn.close()
         
        #check the result is valid
        if result:
            #unpack the tuple - assign names
            email, password = result 
            #ensure inputed email and password match the stored version
            if email == userEmail and password == userPassword:
                response_message = "Sign in was successful"
            else:
                response_message = "Incorrect credentials"
        else:
            response_message = "User not found"
        #return the appropriate message
        return jsonify({"response": response_message}), 200

    except Exception as e:
        # Print the exception for details
        print("Error:", str(e))
        return jsonify({"response": "An error occurred", "details": str(e)}), 500
        
#POST endpoint to store a users chat.
@app.route('/store_chat', methods=['POST'])
def store_chat():
     try:
        data = request.json
        message = data['message']
        email = data["email"]
        chat_name = data["chatName"]
        #connect to database
        conn = connect_to_database()        
        cursor = conn.cursor()
        #insert statement
        cursor.execute("INSERT INTO chattable (useremail, chatname, chatcontent) VALUES (%s, %s, %s)",
            (email, chat_name, message))
        #commit transaction
        conn.commit()
        #close connection
        cursor.close()
        conn.close()
        return jsonify({"response": "Message stored"}), 200
     except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
    
@app.route('/review_sign_in', methods=['POST'])
def review_sign_in():
     try:
        generate_keys()
        data = request.json
        name = data["name"]
        email = data["email"]
        conn = connect_to_database()        
        cursor = conn.cursor()
        query ="select useremail from usertable where useremail = %s"
        cursor.execute(query, (email,))  # Provide parameters as a tuple

        # Fetch one result - result will be a tuple
        result = cursor.fetchone()
        if result == None:
            create_user(email, name)

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"response": "Message stored"}), 200
     except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
    
#Method called if the users sign in is their first sign in.
def create_user(email, name):
    try:   
        conn = connect_to_database()        
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usertable (useremail, UserFirstName) VALUES (%s, %s)",
            (email, name))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500    

#POST endpoint to initiate chat with single agent and user proxy agent.
@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Debugging log for incoming request
        print("Received POST request")
        data = request.json
        message = data['message']
        

        groupchat = autogen.GroupChat(agents=[user_proxy, agent_one], messages=[], max_round=20)
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

        user_proxy.initiate_chat(manager, message=message)
        
        # Extract and print only the content of the messages
        # Initialise an empty list to store message contents
        message_contents = []
        # loop through user_proxy messages
        for role, messages in user_proxy.chat_messages.items():
            #Changed the role name for user display. Initially returned object name.
            for message in messages:
                #append the message
                message_contents.append(f"{ message['content']}")
              # To separate messages for appearance in the console
            print("-" * 50)
        user_proxy.chat_messages.clear()
        #storeChart()
        

        # Return the response and 200 success
        return jsonify({"response": message_contents}), 200
    except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
    
#POST Method to inisialise the team of agents chat.    
@app.route('/chat_team', methods=['POST'])
def chat_team():
    try:
        # Debugging log for incoming request
        print("Received POST request")
        data = request.json
        message = data['message']
        agentOne = data['agentOne']
        agentTwo = data['agentTwo']
        agentThree = data['agentThree']
        # Database connection
        conn = connect_to_database()
        cursor = conn.cursor()

        # Use parameterised query for SQL injection
        # The agents data is extracted from the database to configure the agents.
        query = "SELECT agentspecialisation,agentconfig  FROM agentdata WHERE agentid IN (%s, %s, %s)"
        cursor.execute(query, (agentOne, agentTwo, agentThree))

        # Fetch one result - result will be a tuple
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        print(result)
        
        #https://www.w3schools.com/python/python_tuples_unpack.asp
        (specilisationOne, configurationOne), (specilisationTwo, configurationTwo), (specilisationThree, configurationThree) = result
        
        #refactor agents names for configuration. Ensures the users view of the agent name is not changed when viewed.
        specilisationOne = refactor_agent_name(specilisationOne)
        specilisationTwo = refactor_agent_name(specilisationTwo)
        specilisationThree = refactor_agent_name(specilisationThree)

        #Agents and configurations, extracted pulled from the database
        agent_one = autogen.AssistantAgent(
            name = specilisationOne,
            description = configurationOne,
            #configuration - model use, temperature etc.
            llm_config=llm_config,
        )
        
        agent_two = autogen.AssistantAgent(
            name= specilisationTwo,
            description = configurationTwo,
            llm_config=llm_config,
        )

        agent_three = autogen.AssistantAgent(
            name= specilisationThree,
            description = configurationThree,
            llm_config=llm_config,
        )
        
        #Implement the group chat and pass the user proxy and configured agents
        groupchat = autogen.GroupChat(agents=[user_proxy, agent_one, agent_two, agent_three], messages=[], max_round=20)
        #insert the agents and configuration of the manager
        #the GroupChatManager controls the conversation ensuring agents communicate effectively
        manager = autogen.GroupChatManager(groupchat=groupchat,description = configurationThree, llm_config=llm_config)
        #manager is passed to the user proxy with the users message to initiate the chat.
        user_proxy.initiate_chat(manager, message=message)
        
        # Extract and print only the content of the messages
        # Initialise an empty list to store message contents
        message_contents = []
        # loop through user_proxy messages
        for role, messages in user_proxy.chat_messages.items():
            #Changed the role name for user display. Initially returned object name.
            for message in messages:
                #append the message
                message_contents.append(f"{ message['content']}")
              # To separate messages for appearance in the console
            print("-" * 50)
        user_proxy.chat_messages.clear()
        
        # Return the response and 200 success
        return jsonify({"response": message_contents}), 200
    except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500



@app.route('/retrieve_agents', methods=['POST'])
def retrieve_agents():
    try:
        
        data = request.json
        email = data['email']

            
        #database connection made by calling connect_to _database method
        conn = connect_to_database()
        #cursor object to make connection and execute quesries
        cursor = conn.cursor()
        #select agent specialisation,  agent config, agent id from agent data
        cursor.execute("SELECT agentspecialisation,  agentconfig, agentid FROM agentdata WHERE useremail = %s", (email,))
        #get all the record
        result = cursor.fetchall()
        # format the result to the desired format - making it easier to iterate through on the front end.
        formatted_result = [[[agentspecialisation], [agentconfig], [agentid]] for agentspecialisation, agentconfig, agentid in result]

        print(formatted_result)
        #chech result is valid and set the chat content
        if not result:
            chat_content = "<div id = 'previous_chat_error'><h1 id= 'returned_data'> Error fetching chat data</h1><br /><h3 id = 'previous_chat_error_sub'> Please try again later</h3></div>"  
            return jsonify({"message": chat_content}), 200
        cursor.close()
        conn.close()
        
        return jsonify({"message": formatted_result}), 200
    except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
    
# POST endpoint- Method to store the data required to pull agents configuration when talking with the team.    
@app.route('/store_team', methods=['POST'])
def store_team():
    try:
        data = request.json
        teamName = data['teamName']
        userEmail = data['userEmail']
        
        teamDescription = data['teamDescription']
        agentOne = data['agentOne']
        agentTwo = data['agentTwo']
        agentThree = data['agentThree']
        print(userEmail)
        print(agentTwo)
        print(agentThree)
        
        conn = connect_to_database()        
        cursor = conn.cursor() #creating a new record on the agent teams table.
        cursor.execute("INSERT INTO agentteams (useremail, teamname, teamdescription, teamagentone, teamagenttwo, teamagentthree) VALUES (%s, %s, %s, %s, %s,%s)",
                (userEmail, teamName , teamDescription, agentOne, agentTwo, agentThree ))
        #commit the transaction
        conn.commit()
        #close the connection.
        cursor.close()
        conn.close()
        #return appropriate message
        return jsonify({"response": "Team stored"}), 200
    except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
    
#POST Endpoint - Method to gather all teams created by a user    
@app.route('/gather_teams', methods=['POST'])
def gather_teams():
    try:
        
        data = request.json
        email = data['email']

        #cant remember why implemented - please revisit
        if isinstance(email, str):

            
            #database connection made by calling connect_to _database method
            conn = connect_to_database()
            #cursor object to make connection and execute quesries
            cursor = conn.cursor()
            #select chat with the id of 4 from the chattable 
            cursor.execute("SELECT teamname, teamdescription, teamagentone, teamagenttwo, teamagentthree FROM agentteams WHERE useremail = %s", (email,))
            result = cursor.fetchall()
            formatted_result = [[[teamname], [teamdescription], [teamagentone], [teamagenttwo], [teamagentthree]] for teamname, teamdescription, teamagentone, teamagenttwo, teamagentthree in result]

            print(formatted_result)
            #chech result is valid and set the chat content
            if not result:
                chat_content = "<div id = 'previous_chat_error'><h1 id= 'returned_data'> Error fetching chat data</h1><br /><h3 id = 'previous_chat_error_sub'> Please try again later</h3></div>"  
                return jsonify({"message": chat_content}), 200
            cursor.close()
            conn.close()
        
            
        
        return jsonify({"message": formatted_result}), 200
    except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500

def storePublicKey(key, email):
    try:

        #database connection made by calling connect_to _database method
        conn = connect_to_database()
        #cursor object to make connection and execute quesries
        cursor = conn.cursor()
        #select chat with the id of 4 from the chattable 
        cursor = conn.cursor() #creating a new record on the agent teams table.
        cursor.execute("INSERT INTO userKeys (useremail, publickey, privatekey ) VALUES (%s, %s, %s)",
                (email, ))
        #commit the transaction
        conn.commit()
        result = cursor.fetchall()
        formatted_result = [[[teamname], [teamdescription], [teamagentone], [teamagenttwo], [teamagentthree]] for teamname, teamdescription, teamagentone, teamagenttwo, teamagentthree in result]

        print(formatted_result)
        #chech result is valid and set the chat content
        if not result:
            chat_content = "<div id = 'previous_chat_error'><h1 id= 'returned_data'> Error fetching chat data</h1><br /><h3 id = 'previous_chat_error_sub'> Please try again later</h3></div>"  
            return jsonify({"message": chat_content}), 200
        cursor.close()
        conn.close()
        
            
        
        return jsonify({"message": formatted_result}), 200
    except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
    
def generate_keys():

# Key Length: 2048 bits (recommended for security)
    key_length = 2048

    # Generate RSA Key Pair
    key = RSA.generate(key_length)

    # Export Private Key
    private_key = key.export_key(format='PEM')
    with open('private_key.pem', 'wb') as private_file:
        private_file.write(private_key)

    # Export Public Key
    public_key = key.publickey().export_key(format='PEM')
    with open('public_key.pem', 'wb') as public_file:
        public_file.write(public_key)

    print("RSA Key Pair Generated and Saved:")
    print(private_key)
    print(public_key)
    aes_key = bytes.fromhex(os.getenv('AES_KEY'))
        # Read the private key as bytes
    with open('private_key.pem', 'rb') as private_file:
        private_key_data = private_file.read()
    ciphertext, tag, nonce = encrypt_message(aes_key, private_key_data)
    print(ciphertext,tag, nonce)
    print(decrypt_message(aes_key,ciphertext,tag, nonce))
    

def encrypt_message(aes_key, message):
    #encrypts the given message using AES encryption.
    # aes_key (bytes): The AES key for encryption.
    # message (bytes): The message to be encrypted.
    #returns tuple ciphertext and tag for the encrypted message.
    
    # Create AES cipher in EAX mode
    cipher = AES.new(aes_key, AES.MODE_EAX)
    
    # Encrypt the message and generate the authentication tag
    ciphertext, tag = cipher.encrypt_and_digest(message)
    
    return ciphertext, tag, cipher.nonce

# Method 2: Decrypt the message using AES
def decrypt_message(aes_key, ciphertext, tag, nonce):
   
    #Decrypts the given ciphertext using AES decryption
    
    
    #aes_key (bytes): The AES key for decryption.
    #ciphertext (bytes): The encrypted message to be decrypted.
    #tag (bytes): The authentication tag used for verification.
    #nonce (bytes): The nonce used in the encryption process.   
    #Returns The decrypted message as a string.
    
    # Create AES cipher for decryption using the provided nonce
    decipher = AES.new(aes_key, AES.MODE_EAX, nonce=nonce)
    
    # Decrypt the message and verify the authentication tag
    decrypted_message = decipher.decrypt_and_verify(ciphertext, tag)
    
    return decrypted_message.decode()


if __name__ == '__main__':
    #Both set to false - when files were created, the server was restarting, set to false to overcome issue
    app.run(debug=False, use_reloader=False)
    



