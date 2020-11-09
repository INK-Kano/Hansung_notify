import time
import random
from selenium import webdriver
from bs4 import BeautifulSoup
import sqlite3
import os
import subprocess
from multiprocessing import Pool
import requests


# 동영상
# http://learn.hansung.ac.kr/report/ubcompletion/user_progress_a.php?id=
# 과제
# http://learn.hansung.ac.kr/mod/assign/index.php?id=
# 실강
# http://learn.hansung.ac.kr/mod/webexactivity/index.php?id=
# 인증
# http://learn.hansung.ac.kr/local/ruauth/

def make_db():
    conn.execute(
        "CREATE TABLE IF NOT EXISTS user_data(class_name text, division text, professor text, class_link text, class_link_num text, notice_link_num text)"
    )

    cur.execute(
        "CREATE TABLE IF NOT EXISTS homework(class_name text, title text, due_date text, status text, grade text)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS file(class_name text, title text, description text)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS notice(class_name text, title text, creation_date text)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS quiz(class_name text, title text, due_date text, grade text)"
    )


def get_class():
    cur.execute("SELECT * FROM user_data")

    if len(cur.fetchall()) == 0:
        mainpage = session.get("https://learn.hansung.ac.kr/")

        mainpage_soup = BeautifulSoup(mainpage.text, 'lxml')
        class_infos = mainpage_soup.select('a.course_link')

        for i in class_infos:
            temp = i.text

            if temp.find("커뮤니티") == -1:
                class_name.append(temp[10:temp.find("[")])
                division.append(temp[temp.find("[") + 1])
                professor.append(temp[temp.find("]") + 1:])
                class_link.append(i["href"])
                class_link_num.append(i["href"][-4:])

        for i in range(0, len(class_name)):
            professor[i] = professor[i].replace("NEW", "")

        for i in range(0, len(class_name)):
            notice_temp = session.get("http://learn.hansung.ac.kr/course/view.php?id=" + class_link_num[i])
            notice_temp_soup = BeautifulSoup(notice_temp.text, 'lxml')

            notice_num = notice_temp_soup.select('div.activityinstance > a')
            notice_link.append(notice_num[0]["href"][-6:])

        for i in range(0, len(class_name)):
            cur.execute("INSERT INTO user_data VALUES (?, ?, ?, ?, ?, ?)",
                        (class_name[i], division[i], professor[i], class_link[i], class_link_num[i], notice_link[i]))

        class_name.clear()
        professor.clear()
        division.clear()
        class_link.clear()
        class_link_num.clear()
        notice_link.clear()


def get_var_in_db():
    cur.execute("SELECT class_name, class_link_num, notice_link_num FROM user_data")
    lt = cur.fetchall()

    for i in range(0, class_count):
        class_name.append(lt[i][0])
        class_link_num.append(lt[i][1])
        notice_link.append(lt[i][2])


def get_homework():
    for i in range(0, class_count):
        homework_html = session.get("http://learn.hansung.ac.kr/mod/assign/index.php?id=" + class_link_num[i])
        homework_soup = BeautifulSoup(homework_html.text, 'lxml')

        title = homework_soup.select('td.c1')
        due_date = homework_soup.select('td.c2')
        status = homework_soup.select('td.c3')
        grade = homework_soup.select('td.c4')

        for j in range(0, len(title)):
            cur.execute("INSERT INTO homework VALUES (?, ?, ?, ?, ?)",
                        (class_name[i], title[j].text, due_date[j].text, status[j].text, grade[j].text))


def get_file():
    for i in range(0, class_count):
        file_html = session.get("http://learn.hansung.ac.kr/mod/ubfile/index.php?id=" + class_link_num[i])
        file_soup = BeautifulSoup(file_html.text, 'lxml')

        title = file_soup.select('td.c1')
        description = file_soup.select('td.c2')

        for j in range(0, len(title)):
            cur.execute("INSERT INTO file VALUES (?, ?, ?)",
                        (class_name[i], title[j].text, description[j].text))


def get_notice():
    for i in range(0, class_count):
        notice_html = session.get("http://learn.hansung.ac.kr/mod/ubboard/view.php?id=" + notice_link[i])
        notice_soup = BeautifulSoup(notice_html.text, 'lxml')

        notice_temp = notice_soup('td')

        notice = []
        created_date = []

        print(class_name[i])
        
        for j in range(0, len(notice_temp)):
            notice_temp[j] = notice_temp[j].text.replace("\t", "")
            notice_temp[j] = notice_temp[j].replace("\n", "")

            print(notice_temp[j])
            print("+++++++++++++++++++++++++++++++++++++++++++++++" + str(j) + "+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("==========================================================================================================")

        j = 0
        while len(notice_temp) > j:
            if notice_temp[j] != "등록된 게시글이 없습니다.":
                notice.append(notice_temp[j])
                created_date.append(notice_temp[j])

            j += 1

        for j in range(0, len(notice)):
            f.write(notice[j] + " " + created_date[j] + "\n")


def get_quiz():
    for i in range(0, class_count):
        quiz_html = session.get("http://learn.hansung.ac.kr/mod/quiz/index.php?id=" + class_link_num[i])
        quiz_soup = BeautifulSoup(quiz_html.text, 'lxml')

        title = quiz_soup.select('td.c1')
        due_date = quiz_soup.select('td.c2')
        grade = quiz_soup.select('td.c3')

        for j in range(0, len(title)):
            cur.execute("INSERT INTO quiz VALUES (?, ?, ?, ?)",
                        (class_name[i], title[j].text, due_date[j].text, grade[j].text))


if __name__ == "__main__":
    start = time.time()

    # connect db
    conn = sqlite3.connect("user.db")
    cur = conn.cursor()

    make_db()

    header = {
        'Referer': 'https://learn.hansung.ac.kr/login.php',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0'
    }

    data = {
        'username': '2071396',
        'password': 'dododo2001!',
        'rememberusername': 'on'
    }

    session = requests.session()
    session.post("https://learn.hansung.ac.kr/login/index.php", headers=header, data=data)

    # list
    class_name = []
    professor = []
    division = []
    class_link = []
    class_link_num = []
    notice_link = []

    get_class()

    cur.execute("SELECT count(class_name) from user_data")
    class_count = cur.fetchall()
    class_count = class_count[0][0]

    get_var_in_db()

    f = open("./temp.txt", 'w')

    # get_homework()
    # get_file()
    # get_quiz()
    get_notice()

    conn.commit()
    cur.close()
    conn.close()

    f.close()

    print(time.time() - start)