# Import dependencies
from Bio import Entrez
import re
import matplotlib as mp
from wordcloud import WordCloud
from PIL import Image
import numpy as np
from os.path import exists
import json

# Define all functions
def get_ids_from_query(query, result_number, email):
    """
    access Pubmed and retrieve result_number of IDs of articles found using query
    """
    Entrez.email = email
    handle = Entrez.esearch(db='pubmed', 
                            sort='relevance', 
                            retmax=str(result_number),
                            retmode='xml', 
                            term=query)
    results = Entrez.read(handle)
    return results['IdList']


def fetch_details(id_list, email):
    """
    Use found IDs to retrieve abstracts and other info from Pubmed
    """
    ids = ','.join(id_list)
    Entrez.email = email
    handle = Entrez.efetch(db='pubmed',
                 retmode='text',
                 id=ids,
                 rettype='abstract')
    results = handle.read()
    return results

def save_papers_text_to_disk(query, max_num_papers, email):
    """
    Save the fetched abstracts to disk in papers.txt    
    """
    ids = get_ids_from_query(query, max_num_papers, email)
    content = str(fetch_details(ids, email))# use the sampled IDs to fetch paper full texts

    with open('papers.txt', 'w') as f:
        f.write(content)

def extract_abstracts(input_path):
    """
    Find text piece between author information and the next break line. This should be the Abstract text in most cases.
    """
    with open(input_path, 'r') as f:
        text = f.read()

    author_info_list = []
    for m in re.finditer('Author information: \n', text):
        author_info_list.append(m.end())

    abstract_start_ids = []
    for line_id in author_info_list:
        abstract_start_ids.append(2+line_id+text[line_id:].find("\n\n"))

    abstracts = []
    for line_id in abstract_start_ids:
        abstract_end = text[line_id:].find('\n\n')
        abstracts.append(text[line_id: line_id+abstract_end].replace('\n', ' '))
    
    return abstracts

def check_email(email):
    """
    Check that the email input at least has the correct format
    """
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if(re.fullmatch(regex, email)):
        return True
 
    else: return False

def import_params():
    print("Do you want to import a previously generated json file? (y/n)")
    import_json = input()
    if (import_json.lower() == 'yes') or (import_json.lower() == 'y'):
        import_json = True
    else: import_json = False
    return import_json

def user_interface():
    """
    This function is far from ideal, but it handles all the user interactions.
    It should definitely be broken down and re-structured into multiple functions.
    """
    # Define dictionary for the user-defined settings
    params_dict = {
        'email': '',
        'query': '',
        'bg_color': None,
        'colormap': 'viridis',
        'max_results': 300,
        'mask_name': None,
    }

    confirm = ''
    # At the end we ask for confirmation otherwise repeat input
    while confirm!='yes':

        # Ask for valid email address and check for its validity
        print('Type a valid email address')
        params_dict['email'] = input()
        # Check that the email address has a valid format
        while not check_email(params_dict['email']):
            print('Email not valid')
            print('Type a valid email address')
            params_dict['email'] = input()

        # Define search query
        print('Type Pubmed Advanced query')
        params_dict['query'] = input()
        # Ask for background color
        print('What color do you want for background (white, black, red..)?\n Press Enter for default (transparent)')
        params_dict['bg_color'] = (input() or None)
        # Ask for text colormap
        print('What colormap do you want to use for the text?\n Press Enter for default (viridis)')
        params_dict['colormap'] = str(input() or 'viridis')
        # Check that chosen colormap is a valid matplotlib colormap
        while params_dict['colormap'] not in mp.colormaps:
            print('Colormap does not exist!')
            print('What colormap do you want to use for the text?\n Press Enter for default (viridis)')
            params_dict['colormap'] = str(input() or 'viridis')
        # Define max number of papers to fetch
        print('Input max number of publications to consider.\n Press Enter for default (300)')
        params_dict['max_results'] = int(input() or 300)
        # Ask for the mask
        print('Type name of mask image including format.\n Press Enter for no mask file')
        params_dict['mask_name'] = (input() or None)
        # Check that the file exists
        if params_dict['mask_name'] != None:
            while not exists(params_dict['mask_name']):
                print('I cannot find this file!')
                print('Type name of mask image including format.\n Press Enter for no mask file')
                params_dict['mask_name'] = (input() or None)

        print('\n\n\n===========')                

        print("Input summary:")
        for key, value in params_dict.items():
            print(key, ":" ,value)

        print("Confirm? (yes)")
        confirm = input()
    return params_dict

# Start of program
if __name__ == '__main__':
    if import_params():
        with open('wordcloud_settings.json') as json_file:
            params_dict = json.load(json_file)
    else:
        params_dict = user_interface()
        

    print('OK! Processing..')
    # Define path where to store found papers
    path = "./"

    # Actually find and save papers
    save_papers_text_to_disk(params_dict['query'], params_dict['max_results'], params_dict['email'])
    print('Fetched papers from Pubmed')

    # Read abstracts and image mask
    abstracts = extract_abstracts('papers.txt')
    if params_dict['mask_name']:
        mask = np.asarray(Image.open(params_dict['mask_name']))
    else: mask = params_dict['mask_name']
    # Create wordcloud
    wordcloud = WordCloud(mask=mask, background_color=params_dict['bg_color'], mode="RGBA",
                        colormap=params_dict['colormap'], width=800, height=400).generate(str(abstracts))
    # Export wordcloud
    wordcloud.to_file('wordcloud.png')
    # Export used params
    with open("wordcloud_settings.json", "w") as outfile:
        json.dump(params_dict, outfile)

    print('Wordcloud file saved!')
