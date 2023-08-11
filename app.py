import streamlit as st
from grammar_excerciser import GrammarExcerciser

if 'stage' not in st.session_state:
    st.session_state['stage'] = 0

if 'ex_types' not in st.session_state:
    st.session_state['ex_types'] = []

if 'excercises' not in st.session_state:
    st.session_state['excercises'] = None

if 'error_type' not in st.session_state:
    st.session_state['error_type'] = None

if 'text' not in st.session_state:
    st.session_state['text'] = ''

# read file into str
FILENAME = 'red_cap.txt'
with open(FILENAME) as f:
    plaintext = f.read()

exercise_messages = {'past': 'Select the past tense',
                     'passive': 'Select the verb form',
                     'be': 'Type the proper form of the verb to be',
                     'prep': 'Type the correct preposition'}

def type_excercises():
    ex_list = []
    for item in topics:
        if item == 'Past Simple':
            ex_list.append('past')
        elif item == 'Past Continuous':
            ex_list.append('past')
        elif item == 'Past Perfect':
            ex_list.append('past')
        elif item == 'Passive voice':
            ex_list.append('passive')
        elif item == 'Forms of the verb TO BE':
            ex_list.append('be')
        elif item == 'Prepositions':
            ex_list.append('prep')
    return set(ex_list)

def get_excercises(ge):
    all_exs = []
    for type in st.session_state['ex_types']:
        if type == 'past':
            all_exs.append(ge.get_past_tenses_excercises(num_sentences))
        elif type == 'passive':
            all_exs.append(ge.get_active_passive_excercises(num_sentences))
        elif type == 'be':
            all_exs.append(ge.get_be_excercises(num_sentences))
        elif type == 'prep':
            all_exs.append(ge.get_prep_excercises(num_sentences))
    return all_exs

def set_stage(i):
    st.session_state['stage'] = i

def set_stage_upload_text(text):
    st.session_state['text'] = text
    ge = GrammarExcerciser(text)
    st.session_state['ex_types'] = type_excercises()

    if ge.df.shape[0] < 100:
        set_stage(1)   
        st.session_state['error_type'] = 'too_short' 
    elif len(st.session_state['ex_types']) == 0:
        set_stage(1)      
    else:
        set_stage(2)
        
        st.session_state['excercises'] = get_excercises(ge)

def set_stage_default_text():
    st.session_state['ex_types'] = type_excercises()
    if len(st.session_state['ex_types']) == 0:
        set_stage(1)
    else:
        set_stage(2)    
        ge = GrammarExcerciser(plaintext)    
        st.session_state['ex_types'] = type_excercises()

        
        st.session_state['excercises'] = get_excercises(ge)

def try_another_text():
    set_stage(0)
    st.session_state['text'] = ''
    st.session_state['error_type'] = None

st.header('English language excercises out of a text')
st.write('Here you can practice your English solving excercises generated from a text. Please paste the text you\'d like to practice on into the form below. In case you have no proper text at hand you can still enjoy the excercises made of The Little Red Cap by Wilhelm Grimm')

text = st.text_area('nolabel', value=st.session_state['text'], label_visibility="hidden")

col1, col2 = st.columns(2, gap='large')
with col1:
    num_sentences = st.slider('How many sentences per excercise would you like to get?', 1, 8, 6)
with col2:
    topics = st.multiselect('Which grammar topics would you like to practice?', ['Past Simple', 'Past Continuous', 'Past Perfect', 'Passive voice', 'Forms of the verb TO BE', 'Prepositions'])

col1, col2, col3 = st.columns(3)
with col1:
    st.button('Get excercises', on_click=set_stage_upload_text, args=[text])
with col2:
    st.button('Use default text', on_click=set_stage_default_text)
with col3:
    st.button('Read default text', on_click=set_stage, args=[1])

if st.session_state['stage'] == 1:
    if st.session_state['error_type'] == 'too_short':
        st.write('Sorry, your text seems too short. Please try a text of at least 100 sentences')
        st.button('Try another text', on_click=try_another_text)
    elif len(st.session_state['ex_types']) == 0:
        st.write('No grammar topics are chosen. Please select one or more')
    else:
        st.write(plaintext)
        st.button('Hide text', on_click=back_to_topics)

if st.session_state['stage'] >= 2:

    st.write(st.session_state['ex_types'])
    st.write(st.session_state['excercises'])

    # with st.form('ex_form'):
    #     st.subheader('Choose the right past tense')

    #     for j in range(len(st.session_state['past_excercises'])):
    #         task = st.session_state['past_excercises'][j]
    #         col1, col2 = st.columns(2)
    #         with col1:
    #             st.write('')
    #             st.write(task['sentence'])
                    
    #         with col2:
    #             for i in range(len(task['options'])):
    #                 option = task['options'][i]
    #                 task['result'][i] = st.selectbox('nolabel', 
    #                                                 ['–––'] + option, 
    #                                                 key=str(j) + str(i),
    #                                                 label_visibility="hidden")                    
    #         '---'    

    #     st.form_submit_button("Submit", on_click=set_stage, args=[3])
        
if st.session_state['stage'] >= 3:
    for task in st.session_state['past_excercises']:
        for i in range(len(task['options'])):
            if task['result'][i] == task['answers'][i]:
                task['total'] += 1                    
    st.write(f"{sum([task['total'] for task in st.session_state['past_excercises']])} correct answers out of {sum([len(task['result']) for task in st.session_state['past_excercises']])}")

    for task in st.session_state['past_excercises']:
        sentence_slices = task['sentence'].split('_____')
        correct_sent = []
        for i in range(len(task['options'])):
            correct_sent.append(sentence_slices[i])
            correct_sent.append(f"**:green[{task['answers'][i]}]**")
            if task['result'][i] != task['answers'][i]:
                correct_sent.append(f"_(you've chosen **:red[{task['result'][i]}]**)_")
        correct_sent.append(sentence_slices[-1])
        st.write(' '.join(correct_sent))

    st.button('Try again', on_click=set_stage, args=[0])

    

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