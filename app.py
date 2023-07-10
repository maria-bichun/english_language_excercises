import streamlit as st
import json

with open("past.json") as json_file :
  past_excercises = json.load(json_file)

with open("prep.json") as json_file :
  prep_excercises = json.load(json_file)

st.header('English language excercises out of a text')
st.write('Here you can practice your English solving excercises generated from a text. By design you should be able to upload a text of yours. Waiting for this cool feature to be implemented you can enjoy excercises made of The Little Red Cap by Wilhelm Grimm')

st.subheader('Choose the right past tense')

for task in past_excercises:
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
            if task['result'][i] == '–––':
                pass
            elif task['result'][i] == task['answers'][i]:
                st.success('', icon="✅")
            else:
                st.error('', icon="😟")
    task['total'] = task['result'] == task['answers']    
    '---'        

st.subheader('Fill in the gaps. Type the missing preposition')

for j in range(len(prep_excercises)):
    col1, col2 = st.columns(2)
    with col1:
        st.write('')
        st.write(prep_excercises[j]['sentence'])
        
    with col2:
        for i in range(len(prep_excercises[j]['answers'])):
            
            prep_excercises[j]['result'][i] = st.text_input('nolabel', 
                                             '', 
                                             key=str(j) + str(i),
                                             label_visibility="hidden")
            if prep_excercises[j]['result'][i] == '':
                pass
            elif prep_excercises[j]['result'][i] == prep_excercises[j]['answers'][i]:
                st.success('', icon="✅")
            else:
                st.error('', icon="😟")
    prep_excercises[j]['total'] = prep_excercises[j]['result'] == prep_excercises[j]['answers']    
    '---'        

total_sum = sum(task['total'] for task in past_excercises) + sum(task['total'] for task in prep_excercises)

if total_sum == len(past_excercises) + len(prep_excercises):
    st.success('Well done!')
    st.balloons()