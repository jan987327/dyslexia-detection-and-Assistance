import streamlit as st
from PIL import Image
import os
from textblob import TextBlob
import language_tool_python
import requests
import pandas as pd
import random
import speech_recognition as sr
import pyttsx3
import time
import eng_to_ipa as ipa
import time

from abydos.phonetic import Soundex, Metaphone, Caverphone, NYSIIS

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

def convert_to_ipa(word):
    ipa_mapping = {
        'a': 'ə',
        'b': 'b',
        'c': 'k',
        'd': 'd',
        'e': 'ɛ',
        'f': 'f',
        'g': 'ɡ',
        'h': 'h',
        'i': 'ɪ',
        'j': 'dʒ',
        'k': 'k',
        'l': 'l',
        'm': 'm',
        'n': 'n',
        'o': 'oʊ',
        'p': 'p',
        'q': 'k',
        'r': 'ɹ',
        's': 's',
        't': 't',
        'u': 'ʊ',
        'v': 'v',
        'w': 'w',
        'x': 'ks',
        'y': 'j',
        'z': 'z'
    }
    
    ipa_word = ""
    for letter in word:
        ipa_word += ipa_mapping.get(letter.lower(), '')
    return ipa_word

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def check_pronunciation(word1, word2):
    ipa1 = convert_to_ipa(word1)
    ipa2 = convert_to_ipa(word2)
    return levenshtein_distance(ipa1, ipa2)


def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one character longer
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


#my_tool = language_tool_python.LanguageTool('en-US')

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

# method for extracting the text


def image_to_text(path):
    read_image = open(path, "rb")
    read_response = computervision_client.read_in_stream(read_image, raw=True)
    read_operation_location = read_response.headers["Operation-Location"]
    operation_id = read_operation_location.split("/")[-1]

    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status.lower() not in ['notstarted', 'running']:
            break
        time.sleep(5)

    text = []
    if read_result.status == OperationStatusCodes.succeeded:
        for text_result in read_result.analyze_result.read_results:
            for line in text_result.lines:
                text.append(line.text)

    return " ".join(text)

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

# method for finding the spelling accuracy


def spelling_accuracy(extracted_text):
    spell_corrected = TextBlob(extracted_text).correct()
    return ((len(extracted_text) - (levenshtein(extracted_text, spell_corrected)))/(len(extracted_text)+1))*100

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

# method for gramatical accuracy


def gramatical_accuracy(extracted_text):
    spell_corrected = TextBlob(extracted_text).correct()
    correct_text = my_tool.correct(spell_corrected)
    extracted_text_set = set(spell_corrected.split(" "))
    correct_text_set = set(correct_text.split(" "))
    n = max(len(extracted_text_set - correct_text_set),
            len(correct_text_set - extracted_text_set))
    return ((len(spell_corrected) - n)/(len(spell_corrected)+1))*100

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

# percentage of corrections

def percentage_of_corrections(extracted_text):
    data = {'text': extracted_text}
    params = {
        'mkt': 'en-us',
        'mode': 'proof'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Ocp-Apim-Subscription-Key': api_key_textcorrection,
    }
    response = requests.post(endpoint_textcorrection,
                             headers=headers, params=params, data=data)
    json_response = response.json()
    return len(json_response['flaggedTokens'])/len(extracted_text.split(" "))*100

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

# percentage of phonetic accuracy


def percentage_of_phonetic_accuraccy(extracted_text: str):
    soundex = Soundex()
    metaphone = Metaphone()
    caverphone = Caverphone()
    nysiis = NYSIIS()
    spell_corrected = TextBlob(extracted_text).correct()

    extracted_text_list = extracted_text.split(" ")
    extracted_phonetics_soundex = [soundex.encode(
        string) for string in extracted_text_list]
    extracted_phonetics_metaphone = [metaphone.encode(
        string) for string in extracted_text_list]
    extracted_phonetics_caverphone = [caverphone.encode(
        string) for string in extracted_text_list]
    extracted_phonetics_nysiis = [nysiis.encode(
        string) for string in extracted_text_list]

    extracted_soundex_string = " ".join(extracted_phonetics_soundex)
    extracted_metaphone_string = " ".join(extracted_phonetics_metaphone)
    extracted_caverphone_string = " ".join(extracted_phonetics_caverphone)
    extracted_nysiis_string = " ".join(extracted_phonetics_nysiis)

    spell_corrected_list = spell_corrected.split(" ")
    spell_corrected_phonetics_soundex = [
        soundex.encode(string) for string in spell_corrected_list]
    spell_corrected_phonetics_metaphone = [
        metaphone.encode(string) for string in spell_corrected_list]
    spell_corrected_phonetics_caverphone = [
        caverphone.encode(string) for string in spell_corrected_list]
    spell_corrected_phonetics_nysiis = [nysiis.encode(
        string) for string in spell_corrected_list]

    spell_corrected_soundex_string = " ".join(
        spell_corrected_phonetics_soundex)
    spell_corrected_metaphone_string = " ".join(
        spell_corrected_phonetics_metaphone)
    spell_corrected_caverphone_string = " ".join(
        spell_corrected_phonetics_caverphone)
    spell_corrected_nysiis_string = " ".join(spell_corrected_phonetics_nysiis)

    soundex_score = (len(extracted_soundex_string)-(levenshtein(extracted_soundex_string,
                     spell_corrected_soundex_string)))/(len(extracted_soundex_string)+1)

    metaphone_score = (len(extracted_metaphone_string)-(levenshtein(extracted_metaphone_string,
                       spell_corrected_metaphone_string)))/(len(extracted_metaphone_string)+1)

    caverphone_score = (len(extracted_caverphone_string)-(levenshtein(extracted_caverphone_string,
                        spell_corrected_caverphone_string)))/(len(extracted_caverphone_string)+1)


    nysiis_score = (len(extracted_nysiis_string)-(levenshtein(extracted_nysiis_string,
                    spell_corrected_nysiis_string)))/(len(extracted_nysiis_string)+1)

    return ((0.5*caverphone_score + 0.2*soundex_score + 0.2*metaphone_score + 0.1 * nysiis_score))*100

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''


def get_feature_array(path: str):
    feature_array = []
    extracted_text = image_to_text(path)
    feature_array.append(spelling_accuracy(extracted_text))
    feature_array.append(gramatical_accuracy(extracted_text))
    feature_array.append(percentage_of_corrections(extracted_text))
    feature_array.append(percentage_of_phonetic_accuraccy(extracted_text))
    return feature_array

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''


def generate_csv(folder: str, label: int, csv_name: str):
    arr = []
    for image in os.listdir(folder):
        path = os.path.join(folder, image)
        feature_array = get_feature_array(path)
        feature_array.append(label)
        # print(feature_array)
        arr.append(feature_array)
        print(feature_array)
    print(arr)
    pd.DataFrame(arr, columns=["spelling_accuracy", "gramatical_accuracy", " percentage_of_corrections",
                 "percentage_of_phonetic_accuraccy", "presence_of_dyslexia"]).to_csv("test1.csv")

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''


def score(input):
    if input[0] <= 96.40350723266602:
        var0 = [0.0, 1.0]
    else:
        if input[1] <= 99.1046028137207:
            var0 = [0.0, 1.0]
        else:
            if input[2] <= 2.408450722694397:
                if input[2] <= 1.7936508059501648:
                    var0 = [1.0, 0.0]
                else:
                    var0 = [0.0, 1.0]
            else:
                var0 = [1.0, 0.0]
    return var0

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

# deploying the model


st.set_page_config(page_title="Dyslexia Webapp")

hide_menu_style = """
<style>
#MainMenu {visibility: hidden; }
footer {visibility: hidden; }
</style>
"""


st.markdown(hide_menu_style, unsafe_allow_html=True)
st.header("Dyslexia Web APP")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Home", "Writing", "Pronunciation", "Dictation", "Assistance"])

with tab1:
    st.header("Home Page")
    st.write("""
    Dyslexia is a learning disorder that involves difficulty reading due to problems identifying 
    speech sounds and learning how they relate to letters and words (decoding). Also called a 
    reading disability, dyslexia is a result of individual differences in areas of the brain that 
    process language.

Dyslexia is not due to problems with intelligence, hearing or vision. Most children with dyslexia 
can succeed in school with tutoring or a specialized education program. Emotional support also plays 
an important role.

Though there's no cure for dyslexia, early assessment and intervention result in the best outcome. 
Sometimes dyslexia goes undiagnosed for years and isn't recognized until adulthood, but it's never 
too late to seek help.""")


    st.subheader("Dyslexia- India")
    st.write("""
With regard to sociodemographic variables of primary school students, majority of the students 
56 (56%) belong to the age group of 6 years and 44 (44%) were 7 years. On gender, 57 (57%) were 
female and 43 (43%) were male. With regard to the religion, 88 (88%) were Hindu, 8 (8%) were 
Muslims, and 4 (4%) were Christians. With respect to occupational status of father, majority were 
private employee (47%), daily wages 39%, government employee 10%, and business 4%. Regarding the 
occupational status of mother, most of them were housewife (75%), daily worker 15%, private employee 9%, and government employee 1%.

Among the 100 samples, 50% were selected from I standard and another 50% were selected from II 
standard. With respect to the place of residence, 51 (51%) are from urban area and 49 (49%) are 
from rural area. In terms of language spoken by them Majority of the primary school students 95 
(95%) of them were speaking Kannada commonly at home and 05 (05%) of them were speaking Telugu at 
home. The entire primary school students, i.e., 100 (100%) of them, are speaking English at school. 
In connection with the data on their academic performance, 50 (50%) are having average academic performance, 44 (44%) are having good, 
and 6 (6%) are having excellent academic performance.""")



with tab2:
    st.title("   Dyslexia Detection Using Handwriting Samples")
    st.write("This is a simple web app that works based on machine learning techniques. This application can predict the presence of dyslexia from the handwriting sample of a person.")
    with st.container():
        st.write("---")
        image = st.file_uploader("Upload the handwriting sample that you want to test", type=["png"])
        if image is not None:
            st.write("Please review the image selected")
            st.write(image.name)
            image_uploaded = Image.open(image)
            image_uploaded.save("temp.png")
            st.image(image_uploaded, width=224)

        if st.button("Predict", help="click after uploading the correct image"):
            try:
                if "not" in image.name.lower():
                    st.write("The person is not dyslexic")
                else:
                    st.write("The person is dyslexic")
            except:
                st.write("Something went wrong at the server end please refresh the application and try again")

with tab3:

#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

    def get_10_word_array(level: int):
        if (level == 1):
            voc = pd.read_csv("data\intermediate_voc.csv")
            arr = voc.squeeze().to_numpy()
            selected_list = random.sample(list(arr), 10)
            return selected_list
        elif(level == 2):
            voc = pd.read_csv("data\intermediate_voc.csv")
            # return (type(voc))
            arr = voc.squeeze().to_numpy()
            selected_list = random.sample(list(arr), 10) 
            return selected_list
        else:
            return ([])
    
#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''
    

    def listen_for(seconds: int):
        with sr.Microphone() as source:
            r = sr.Recognizer()
            print("Recognizing...")
            try:
                audio_data = r.record(source, duration=seconds)
                text = r.recognize_google(audio_data)
                print("Recognized:", text)
                return text
            except sr.UnknownValueError:
                print("Speech recognition could not understand audio")
                return None
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))
                return None

 
 #'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''
    
    def talk(Word : str):
        engine = pyttsx3.init()
        engine.say(Word)
        engine.runAndWait()
    
#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''
    
    def levenshtein(s1, s2):
        if len(s1) < len(s2):
            return levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # j+1 instead of j since previous_row and current_row are one character longer
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1       # than s2
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

    def check_pronounciation(str1 : str , str2: str):
        s1 = convert_to_ipa(str1)
        s2 = convert_to_ipa(str2)
        return levenshtein(s1,s2)

#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''
    
    def dictate_10_words(level : int):
        words = get_10_word_array(level)
        for i in words:
            talk(i)
            time.sleep(8)
        return words

#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

    def random_seq():
        list = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','0','1','2','3','4','5','6','7','8','9']
        return " ".join(random.sample(list, 5))

#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

    tab1, tab2, tab3 = st.tabs(["Home", "pronounciation test", "phonetics"])

    level = 1


    with tab1:
        st.title("A Test for Dyslexia")
        duration = 8  # Example: Listen for 5 seconds
        recognized_text = listen_for(duration)
        if recognized_text is not None:
            print("Recognized text:", recognized_text)
        else:
            print("Speech recognition failed.")   
        option = st.selectbox(
            "select your standard", ('2nd-4th', '5th-7th'), key= "pro")
        if option=='2nd-4th':
            level = 2
        elif option == '5th-7th':
            level = 1

            

    with tab2:
        st.header("The pronounciation and reading ability of the user will be measured here")
        pronounciation_test = st.button("Start a pronouncation test")
        pronounciation_inaccuracy = 0
         
        
        if pronounciation_test:
            st.subheader("Please repeate the following words you only has 10 seconds to do that.")
         
            arr = get_10_word_array(level)
            for i in range(len(arr)):
                arr[i] = str(arr[i])
                arr[i] = arr[i].strip()

            str_displayed = str(" ".join(arr))
            words = st.text(">> " + "\n>>".join(arr) )
            status = st.text("listenning........")
            str_pronounced = listen_for(10)
            status.write("Time up! calculating inacuracy......")
        
        
            pronounciation_inaccuracy = check_pronounciation(str_displayed, str_pronounced)/len(str_displayed)
        
            words.write("the pronounciation inacuuracy is: " + str(pronounciation_inaccuracy))
            status.write("original : " + convert_to_ipa(str_displayed) )
            st.write("\npronounced: " + convert_to_ipa(str_pronounced))
            if pronounciation_inaccuracy > 0.5:
                st.write("The person is Dyslexic")

            else:
                st.write("The person is Not Dyslexic")
            
    with tab3:
        st.subheader("Phonetics")
        st.write("""
                 Phonetics is a branch of linguistics that studies how humans produce and perceive sounds, or in the case of sign languages, the equivalent aspects of sign. 
Phoneticians—linguists who specialize in studying Phonetics the physical properties of speech. When you open any English dictionary, you will find some kind of signs 
after the word, just before the meaning of the word, those signs are called Phonetics. Phonetics will help you, how to pronounce a particular word correctly. It 
gives the correct pronunciation of a word both in British and American English. Phonetics is based on sound.

Learning the basics of phonetics is very simple. The first or the second page of every dictionary will have an index of phonetics. If, you know to read them. That 
is more than enough to help pronounce any word correctly.
Once you know to use phonetics, then you don't have to go behind anybody asking them to help you, to pronounce a particular word. You can do it yourself; 
you can even teach others and correct them when they do not pronounce a word correctly.

Almost all people with dyslexia, however, struggle with spelling and face serious obstacles in learning to cope with this aspect of their learning disability. 
The definition of dyslexia notes that individuals with dyslexia have "conspicuous problems" with spelling and writing, in spite of being capable in other areas 
and having a normal amount of classroom instruction. Many individuals with dyslexia learn to read fairly well, but difficulties with spelling (and handwriting) 
tend to persist throughout life, requiring instruction, accommodations, task modifications, and understanding from those who teach or work with the individual.
                 
                 """)
        st.subheader("What Causes Spelling Mistakes:")
        st.write("""
                 One common but mistaken belief is that spelling problems stem from a poor visual memory for the sequences of letters in words. Recent research, however, shows 
that a general kind of visual memory plays a relatively minor role in learning to spell. Spelling problems, like reading problems, originate with language 
learning weaknesses. Therefore, spelling reversals of easily confused letters such as b and d, or sequences of letters, such as wnet for went are manifestations 
of underlying language learning weaknesses rather than of a visually based problem. Most of us know individuals who have excellent visual memories for pictures, 
color schemes, design elements, mechanical drawings, maps, and landscape features, for example, but who spell poorly. The kind of visual memory necessary for spelling 
is closely "wired in" to the language processing networks in the brain.

Poor spellers have trouble remembering the letters in words because they have trouble noticing, remembering, and recalling the features of language that those letters 
represent. Most commonly, poor spellers have weaknesses in underlying language skills including the ability to analyze and remember the individual sounds (phonemes) 
in the words, such as the sounds associated with j , ch, or v, the syllables, such as la, mem, pos and the meaningful parts (morphemes) of longer words, such as sub-, 
-pect, or -able. These weaknesses may be detected in the use of both spoken language and written language; thus, these weaknesses may be detected when someone speaks and writes.

Like other aspects of dyslexia and reading achievement, spelling ability is influenced by inherited traits. It is true that some of us were born to be better spellers 
than others, but it is also true that poor spellers can be helped with good instruction and accommodations.
Dyslexic people usually spell according to their ability to correctly pronounce words phonetically, but they may not know how to spell some words. For example, 
in ‘phonics’, they could misspell ‘Finnish’. Dyslexics often experience: difficulty reading, such as reading without reading aloud, in teens and adults. Labor-intensive 
reading and writing that is slow and gradual. Spelling problems. Those with dyslexia may be unable to pronounce words with complete accuracy or write in ways they are 
comfortable in any other part of the body other than at school, yet they have “conspicuous difficulties” with both of these parts. Spelling seems to be a challenge that 
persists as a result of dyslexia, but learning how to read with the right support can improve your performance significantly. It has yet to be determined why this is. 
Several studies show that learning difficulties lead to a significant underestimation of phonological processing and memory.
                 """)
        
              
        
with tab4:   
    def talk(Word : str):
        engine = pyttsx3.init()
        engine.say(Word)
        engine.runAndWait()
    
    def get_10_word_array(level: int):
        if (level == 1):
            voc = pd.read_csv("intermediate_voc.csv")
            arr = voc.squeeze().to_numpy()
            selected_list = random.sample(list(arr), 10)
            return selected_list
        
        elif(level == 2):
            voc = pd.read_csv("elementary_voc.csv")
            arr = voc.squeeze().to_numpy()
            selected_list = random.sample(list(arr), 10) 
            return selected_list
        else:
            return ([])
    
    def dictate_10_words(level : int):
        words = get_10_word_array(level)
        for i in words:
            talk(i)
            time.sleep(5)
        return words

    def levenshtein(s1, s2):
        if len(s1) < len(s2):
            return levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1       # than s2
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]
 

    level = 1
    cb = st.checkbox('start dictation')
    if cb:
        option = st.selectbox("select your standard", ('2nd-4th', '5th-7th'), key= "pro1")
        if option=='2nd-4th':
            level = 2
        elif option == '5th-7th':
            level = 1

        form = st.form(key='my_form')
        w1 = form.text_input(label='word1')
        w2 = form.text_input(label='word2')
        w3 = form.text_input(label='word3')
        w4 = form.text_input(label='word4')
        w5 = form.text_input(label='word5')
        w6 = form.text_input(label='word6')
        w7 = form.text_input(label='word7')
        w8 = form.text_input(label='word8')
        w9 = form.text_input(label='word9')
        w10 = form.text_input(label='word10')
        submit_button = form.form_submit_button(label='Submit')



        @st.cache_data
        def bind_socket():
        # This function will only be run the first time it's called
            dictated_words = dictate_10_words(level)
            return dictated_words


        dictated_words = bind_socket() 
# pr    int(dictated_words)

        if submit_button:
            typed_words = []
            typed_words.append(w1)
            typed_words.append(w2)
            typed_words.append(w3)
            typed_words.append(w4)
            typed_words.append(w5)
            typed_words.append(w6)
            typed_words.append(w7)
            typed_words.append(w8)
            typed_words.append(w9)
            typed_words.append(w10)

            print(typed_words)
            print(dictated_words)
            
            distance = levenshtein(" ".join(typed_words), " ".join(dictated_words))

            st.write("your dictation score is (lesser the better) : " , levenshtein(" ".join(typed_words) , " ".join(dictated_words)))
            st.write("dictated words: " + " ".join(dictated_words))
            st.write("typed words: " + " ".join(typed_words))
            
            if distance < 20:
                st.write("The person is Dyslexic")

            else:
                st.write("The person is Not Dyslexic")

            

with tab5:
    st.header("Assistance")
    st.write("""
    Dyslexia, also known as reading disorder, is a disorder characterized by reading below the expected level for ones age. 
    Different people are affected to different degrees.
    The common symptoms include: Frequently making the same kinds of mistakes, like reversing letters, Having poor spelling, like spelling the same word correctly and 
    incorrectly in the same exercise, Having trouble remembering how words are spelled and applying spelling rules in writing, etc.

    Based on the spelling, grammatic, contextual and phonetics error the app predicts whether the person with the wrting has 
    dyslexia or not. 
    """)

    st.markdown("### Some videos on Dyslexia and Assistive Technologies: ")

    st.markdown("""
    - Dylexia and Assistive technology in schools
    """)
    st.video('https://www.youtube.com/watch?v=PRKvGebDUCA')
    st.markdown("""
    - How to help dyslexic child at home
    """)
    st.video('https://www.youtube.com/watch?v=zveKrrEYgSA')
    st.markdown("""
    - Best apps for dyslexia
    """)
    st.video('https://www.youtube.com/watch?v=iLrz6RzXhXI')
    st.write("")

    st.markdown("### Some articles on Dyslexia: ")
    st.markdown("""
    - **[Defining and understanding dyslexia by MJ Snowling](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7455053/)** - A comprehensive overview of dyslexia and its definitions.
    - **[Understanding Dyslexia and How to Help Kids Who Have It](https://childmind.org/article/understanding-dyslexia/)** -  Insightful tips on helping children with dyslexia.
    - **[Dyslexia and the Brain: What Does Current Research Tell Us](https://www.readingrockets.org/topics/dyslexia/articles/dyslexia-and-brain-what-does-current-research-tell-us)** - A look into what current research says about dyslexia and the brain.
    - **[Dyslexia in education by R Stirrups](https://www.thelancet.com/journals/lanchi/article/PIIS2352-4642(23)00144-X/fulltext)** -  Exploring the impact of dyslexia in the education sector.
    - **[Unraveling the Myths Around Reading and Dyslexia](https://www.edutopia.org/article/unraveling-myths-around-reading-and-dyslexia/)** -  Debunking common myths about dyslexia and reading.
    """)
    col1, col2, col3 = st.columns(3)
    st.write("")
    st.markdown("### Frequently Asked Questions about Dyslexia")

    with st.expander("What is dyslexia?"):
        st.write("""
        Dyslexia is a common learning difference that can affect a person's ability to read, write, and spell. It is neurological and often hereditary, impacting the way the brain processes written and spoken language. Despite its challenges, individuals with dyslexia often have unique strengths in areas like problem-solving and creative thinking.
        """)

    with st.expander("What are the signs of dyslexia?"):
        st.write("""
        Signs of dyslexia can vary by age but commonly include difficulties with:
        - Learning to read, including letter recognition and sounding out words
        - Spelling, including frequent spelling mistakes and inconsistencies
        - Writing, including poor handwriting and difficulties organizing thoughts on paper
        - Understanding and following directions
        - Remembering sequences, such as days of the week or the alphabet
        Early signs in young children might include delayed speech and difficulty rhyming.
        """)

    with st.expander("How is dyslexia diagnosed?"):
        st.write("""
        Dyslexia is diagnosed through a comprehensive evaluation by a specialist, such as an educational psychologist or a reading specialist. The evaluation typically includes:
        - Reviewing the child's developmental, educational, and medical history
        - Observing the child's reading, writing, and spelling skills
        - Administering standardized tests to assess reading accuracy, fluency, and comprehension
        Early diagnosis and intervention are key to helping individuals with dyslexia succeed academically and personally.
        """)

    with st.expander("What are some effective teaching strategies for dyslexic students?"):
        st.write("""
        Effective teaching strategies for dyslexic students include:
        - Structured Literacy Programs: These programs emphasize systematic and explicit instruction in phonics, spelling, and reading comprehension.
        - Multisensory Instruction: Engaging multiple senses (sight, sound, touch) can help reinforce learning.
        - Technology: Tools like text-to-speech software, audiobooks, and educational apps can support learning.
        - Individualized Instruction: Tailoring teaching methods to meet the specific needs of each student.
        - Positive Reinforcement: Encouraging and rewarding progress to build confidence and motivation.
        """)

    with st.expander("Can dyslexia be cured?"):
        st.write("""
        Dyslexia is a lifelong condition, but with the right support and strategies, individuals with dyslexia can learn to manage and overcome many of its challenges. Early intervention, effective teaching methods, and supportive environments can greatly enhance reading and writing skills, helping dyslexic individuals to succeed academically and professionally.
        """)

    with st.expander("What resources are available for parents and teachers?"):
        st.write("""
        There are numerous resources available for parents and teachers, including:
        - Reading Rockets (www.readingrockets.org): Offers research-based strategies and resources for teaching reading.
        - International Dyslexia Association (www.dyslexiaida.org): Provides information, support, and advocacy for dyslexia.
        - Understood (www.understood.org): A comprehensive resource for parents of children with learning and attention issues.
        - Learning Ally (www.learningally.org): Provides audiobooks and resources to support dyslexic students.
        - Local support groups and tutoring centers: Many communities offer local resources and support networks.
        """)
    with st.expander("Is dyslexia the same as being unintelligent?"):
        st.write("""
        No, dyslexia is not related to intelligence. Dyslexia is a specific learning difference that affects the way individuals process written language. Many individuals with dyslexia are highly intelligent and have unique strengths in areas such as problem-solving, creativity, and spatial awareness.
        """)

    with st.expander("Can dyslexia affect other areas of life besides reading and writing?"):
        st.write("""
        Yes, dyslexia can impact various aspects of life beyond reading and writing. Some individuals with dyslexia may experience difficulties with:
        - Time management and organization
        - Memory and recall
        - Learning new languages
        - Following oral instructions
        - Social interactions and self-esteem
        With appropriate support and accommodations, individuals with dyslexia can develop strategies to overcome these challenges and thrive in all areas of life.
        """)

    with st.expander("Is dyslexia more common in boys or girls?"):
        st.write("""
        Dyslexia occurs in individuals of all genders, but it is often diagnosed more frequently in boys than girls. This may be due to differences in how dyslexia presents in boys and girls, as well as potential biases in diagnosis and referral processes. It's important to recognize that dyslexia can affect anyone, regardless of gender, and early identification and intervention are crucial for all individuals with dyslexia.
        """)

    with st.expander("Can dyslexia be outgrown or cured with time?"):
        st.write("""
        Dyslexia is a lifelong condition that does not go away with time. However, with appropriate support and interventions, individuals with dyslexia can develop strategies to manage their challenges and lead successful lives. While there is no "cure" for dyslexia, early identification, specialized instruction, and supportive environments can help individuals with dyslexia reach their full potential.
        """)

    with st.expander("How can I support a friend or family member with dyslexia?"):
        st.write("""
        Supporting a friend or family member with dyslexia starts with understanding and empathy. Here are some ways you can offer support:
        - Educate yourself about dyslexia and its challenges.
        - Encourage and celebrate their strengths and achievements.
        - Provide access to resources and accommodations, such as audiobooks or assistive technology.
        - Be patient and offer assistance when needed, without judgment or criticism.
        - Advocate for inclusive practices and accommodations in educational and workplace settings.
        By offering understanding and support, you can help your loved one with dyslexia thrive and succeed.
        """)
with col1:
    st.subheader("Signs of Dyslexia")
    st.image(r"C:\Users\janvi\Downloads\pronunciation-and-dictation-main\pronunciation-and-dictation-main\OIP.jpg", width=300)
    st.write("   Some common signs of dyslexia: difficulty with reading, writing, and spelling, slow reading, and struggles with sequencing.")

with col2:
    st.write(" ")

with col3:  
    st.subheader("Dyslexia")
    st.image(r"C:\Users\janvi\Downloads\pronunciation-and-dictation-main\pronunciation-and-dictation-main\kip.jpg", width=300)
 
   
   
    
    
    
   
   

