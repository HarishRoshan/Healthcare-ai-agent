\# Healthcare AI Agent



A Python-based conversational AI prototype that uses OpenAI function calling to retrieve fictional patient appointment information and patient status.



\## Project Overview



This project demonstrates foundational Agentic AI engineering concepts, including tool calling, input validation, conversation context, and error handling.



The agent can interpret natural-language questions, select appropriate Python functions, retrieve information, and generate responses based on tool results.



\## Features



\- Natural-language healthcare information queries

\- Two custom tools: appointment count and patient status

\- Multiple tool calls within one request

\- Conversation context using the OpenAI Responses API

\- Input validation using Pydantic

\- Error handling for invalid and unknown patient IDs

\- Interactive command-line interface



\## Technologies Used



\- Python

\- OpenAI API (`gpt-4.1-mini`)

\- Pydantic

\- JSON

\- Git



\## Example Interaction



\*\*User:\*\* How many appointments does patient 102 have?



\*\*AI:\*\* Patient 102 has 3 appointments.



\*\*User:\*\* What is their status?



\*\*AI:\*\* Patient 102 is Active.



\*\*User:\*\* How many appointments does patient 999 have?



\*\*AI:\*\* Patient 999 was not found in the system.



\## Getting Started



1\. Clone this repository.

2\. Create and activate a Python virtual environment.

3\. Install the required packages:



&#x20;  `pip install openai pydantic`



4\. Set your `OPENAI\_API\_KEY` environment variable.

5\. Run the application:



&#x20;  `python healthcare\_agent.py`



6\. Type `exit` to close the application.



\## Safety and Limitations



This is an educational prototype using fictional patient data. It is not connected to NHS systems or real patient records.



It is not suitable for clinical use. A production healthcare application would require authentication, patient-level authorisation, secure data handling, privacy controls, and comprehensive testing.



\## Future Improvements



\- Automated testing with pytest

\- Persistent conversation storage

\- Secure database integration

\- Structured logging and monitoring

\- Authentication and role-based access control

\- Web interface for users



