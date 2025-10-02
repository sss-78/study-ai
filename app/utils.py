import ollama
import textwrap

def prettify_summary(text):
    text = text.replace("**", "")
    wrapped = textwrap.fill(text, width=80)
    return wrapped

def summarize_notes(txt_input, file_input):
    if not txt_input and not file_input:
        return "No input provided."
    
    response = ''
    prompt = \
    '''
    If user gives image input, do the following:
        - First, understand what the image is
        - Then, summarize the information in a clear and concise manner
        - If the user provides an image which is hard to decipher/not very relevant:
            - Then just mention what you see
        - If this content input includes ~.+, then please summarize the text input the user provided,
            if the content after ~.+ provides details about the image the user inputted please feel free 
                to summarize based off that
    If user does not provide image:
        - They must have provided text input so summarize that section
    Additional:
        By summarize, give a summary of the information, provide main ideas, and also provide some questions 
            to think about to further induce additional thought
    '''

    prompt = 'You are a helpful assistant that helps people summarize their notes.'

    if txt_input:
        prompt += '~.+' + txt_input
    images = [file_input] if file_input else []

    try:
        response = ollama.chat(
            model='llama3.2-vision',
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': images
            }]
        )
        response = response['message']['content']
    except Exception as e:
        response = 'ERROR:', str(e)
    
    print(response)
    return response
