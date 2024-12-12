import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import autogen
import psycopg2
import dotenv

app = Flask(__name__)
#used to overcome CORS Policy issues.
CORS(app)

dotenv.load_dotenv()
DATABASE_URL = os.getenv('OPEN_AI_KEY')
DATABASE_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME')
DATABASE_PORT = os.getenv('DATABASE_PORT')


# config_list = autogen.config_list_from_dotenv(
#     dotenv_file_path=".env",
#     model_api_key_map={"gpt-4o": "OPEN_AI_KEY"}
# )

llm_config = {

    #Temerature determines the creativity of response
    "temperature": 0,
    #config list to pass agent model and api key variable
    "config_list": [{"model": 'gpt-4o', 'api_key': DATABASE_URL}],
    #Currently set to none - will configure according after testing
    "timeout": None,
}

user_proxy = autogen.UserProxyAgent(
    #give user proxy a name
    name="User_proxy",
    # execution parameter to be passed to proxy
    code_execution_config={
        #only take the last number messages of conversation
        "last_n_messages": 2,
        #directory to execute scripts and save files to.
        "work_dir": "groupchat",
        #setting if docker is in use to false
        "use_docker": False,
    },  # Please set use_docker=True if docker is available to run the generated code. 
        #Using docker is safer than running the generated code directly.
    ##Currently never taking user input after first input
    human_input_mode="NEVER",
    # Max number of auto repliesbefore terminating conversation.
    max_consecutive_auto_reply=2,
)

# Currently the Agents have minimal configuration to troublshoot user proxy incorrectly functioning.
coder = autogen.AssistantAgent(
    name="Python_Coder",
    #system_message= "First word in every response 'Writer: '",
    llm_config=llm_config,
)
multi_use_agent = autogen.AssistantAgent(
    name="Writing_specialist",
    #system_message= "First word in every response 'Writer: '",
    llm_config=llm_config,
)

multi_use_agent2 = autogen.AssistantAgent(
    name="Information_technology_master",
    #system_message= "Information Tech Master: as the first word",
    llm_config=llm_config,
)
#method to connec to the database
def connect_to_database():
    #pass database name, hostname, username
    conn = psycopg2.connect(database=DATABASE_NAME,
                            host=DATABASE_HOST,
                            user=DATABASE_USERNAME,
                            password=DATABASE_PASSWORD,
                            port=DATABASE_PORT)
    return conn

# GET request endpoint - method to return a full chat
@app.route('/get_previous_chat', methods=['GET'])
def get_previous_chat():
    try:
        #database connection made by calling connect_to _database method
        conn = connect_to_database()
        #cursor object to make connection and execute quesries
        cursor = conn.cursor()
        #select chat with the id of 4 from the chattable 
        cursor.execute("SELECT chatcontent FROM chattable WHERE chatid = 5")
        #fetchone used to grab single row
        result = cursor.fetchone()
        
        #chech result is valid and set the chat content
        if result:
            chat_content = result[0]
        else:
            chat_content = "<div id = 'previous_chat_error'><h1 id= 'returned_data'> Error fetching chat data</h1><br /><h3 id = 'previous_chat_error_sub'> Please try again later</h3></div>"  
        
        cursor.close()
        conn.close()
        
        return jsonify({"message": chat_content}), 200
    except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
    

@app.route('/sign_in_user', methods=['POST'])
def sign_in_user():
    try:
        # Retrieve JSON data from the body
        data = request.json
        
        userEmail = data.get('emailAddress')
        userPassword = data.get('password')  
        
        # Database connection
        conn = connect_to_database()
        cursor = conn.cursor()

        # Use parameterised query for SQL injectio
        query = "SELECT useremail, userpassword FROM usertable WHERE useremail = %s"
        cursor.execute(query, (userEmail,))  # Provide parameters as a tuple

        # Fetch one result - result will be a tuple
        result = cursor.fetchone()
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
            print("User not found")
            response_message = "User not found"

        return jsonify({"response": response_message}), 200

    except Exception as e:
        # Print the exception for details
        print("Error:", str(e))
        return jsonify({"error": "An error occurred", "details": str(e)}), 500
        

    
 
    
    
    



@app.route('/store_chat', methods=['POST'])
def store_chat():
     try:
        data = request.json
        message = data['message']
        conn = connect_to_database()        
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chattable (useremail, chatname, chatcontent) VALUES (%s, %s, %s)",
            ('cra@gg.com', 'chatty', message))
        conn.commit()
        cursor.close()
        conn.close()
        print(message)
        return jsonify({"response": "Message stored"}), 200
     except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
    
@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Debugging log for incoming request
        print("Received POST request")
        data = request.json
        message = data['message']

        groupchat = autogen.GroupChat(agents=[user_proxy, coder, multi_use_agent,multi_use_agent2], messages=[], max_round=20)
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
        user_proxy.chat_messages.clear
        #storeChart()
        

        # Return the response and 200 success
        return jsonify({"response": message_contents}), 200
    except Exception as e:
        # print the exception for details
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
    

if __name__ == '__main__':
    #Both set to false - when file were created the server was restarting, set to false to overcome issue
    app.run(debug=False, use_reloader=False)



