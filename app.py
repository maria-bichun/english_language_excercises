import streamlit as st
import json
from grammar_excerciser import GrammarExcerciser



if 'stage' not in st.session_state:
    st.session_state['stage'] = 0

if 'past_excercises' not in st.session_state:
    st.session_state['past_excercises'] = None

# if 'user_text' not in st.session_state:
#     st.session_state['user_text'] = False

def set_stage(i):
    st.session_state['stage'] = i

def set_stage_upload_text():
    set_stage(1)
    st.session_state['user_text'] = True
    st.write('generate excercises out of your text')

def set_stage_default_text():
    set_stage(1)
    FILENAME = 'red_cap.txt'

    # read file into str
    with open(FILENAME) as f:
        plaintext = f.read()
    ge = GrammarExcerciser(plaintext)
    st.write('generate excercises out of Red Cap fairytale (default)')

    st.session_state['past_excercises'] = ge.get_past_tenses_excercises(2)


# with open("past.json") as json_file:
#     past_excercises = json.load(json_file)

with open("prep.json") as json_file :
  prep_excercises = json.load(json_file)

st.header('English language excercises out of a text')
st.write('Here you can practice your English solving excercises generated from a text. By design you should be able to upload a text of yours. Waiting for this cool feature to be implemented you can enjoy excercises made of The Little Red Cap by Wilhelm Grimm')

text = st.text_area(label='Put your text here')
st.button('Get excercises', on_click=set_stage_upload_text)
st.button('Use default text', on_click=set_stage_default_text)

if st.session_state['stage'] >= 1:

    with st.form('ex_form'):
        st.subheader('Choose the right past tense')

        for task in st.session_state['past_excercises']:
            col1, col2 = st.columns(2)
            with col1:
                st.write('')
                st.write(task['sentence'])
                    
            with col2:
                for i in range(len(task['options'])):
                    option = task['options'][i]
                    task['result'][i] = st.selectbox('nolabel', 
                                                    ['–––'] + option, 
                                                    label_visibility="hidden")
                    # if task['result'][i] == '–––':
                    #     pass
                    # elif task['result'][i] == task['answers'][i]:
                    #     st.success('', icon="✅")
                    # else:
                    #     st.error('', icon="😟")
            # task['total'] = task['result'] == task['answers']    
            '---'    

        submitted = st.form_submit_button("Submit")
        if submitted:
            for task in st.session_state['past_excercises']:
                for i in range(len(task['options'])):
                    if task['result'][i] == task['answers'][i]:
                        task['total'] += 1                    
            st.write(f"{sum([task['total'] for task in st.session_state['past_excercises']])} correct answers out of {sum([len(task['result']) for task in st.session_state['past_excercises']])}")
    

    # st.subheader('Fill in the gaps. Type the missing preposition')

    # for j in range(len(prep_excercises)):
    #     col1, col2 = st.columns(2)
    #     with col1:
    #         st.write('')
    #         st.write(prep_excercises[j]['sentence'])
            
    #     with col2:
    #         for i in range(len(prep_excercises[j]['answers'])):
                
    #             prep_excercises[j]['result'][i] = st.text_input('nolabel', 
    #                                             '', 
    #                                             key=str(j) + str(i),
    #                                             label_visibility="hidden")
    #             if prep_excercises[j]['result'][i] == '':
    #                 pass
    #             elif prep_excercises[j]['result'][i] == prep_excercises[j]['answers'][i]:
    #                 st.success('', icon="✅")
    #             else:
    #                 st.error('', icon="😟")
    #     prep_excercises[j]['total'] = prep_excercises[j]['result'] == prep_excercises[j]['answers']    
    #     '---'        

    # total_sum = sum(task['total'] for task in past_excercises) + sum(task['total'] for task in prep_excercises)

    # if total_sum == len(past_excercises) + len(prep_excercises):
    #     st.success('Well done!')
    #     st.balloons()