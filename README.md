<h4 align="center"> 2025-Summer-Bootcamp-Team-B 🔥

<h1 align="center"> 요즘N </h1>
<div align="center"> 
<h3><b>📚 실시간 뉴스, AI 요약, 관심 키워드까지 한 번에 </b></h3><br>
<img width="1503" src="https://github.com/user-attachments/assets/82652d6f-2deb-4109-aeb3-c55dd14246c4">

<br>

</div>
<br><br>

# 📖 Table of contents
* [Introduction](#-introduction)
* [Medium](#-Medium)
* [Demo](#-demo)
* [API](#-api)
* [System Architecture](#-system-architecture)
* [ERD](#-erd)
* [Tech Stack](#-tech-stack)
* [Monitoring](#-monitoring)
* [How to start](#-how-to-start)
* [Team Members](#-team-members)

<br>

# 📣 Introduction

요즘N은 실시간 뉴스 요약, 관심사 기반 큐레이션, 키워드 유사도 추천, 뉴스 대화형 챗봇 기능을 제공하는 AI 기반 뉴스 브리핑 앱입니다.

사용자는 아침과 저녁, 혹은 출퇴근길에 짧은 시간 내에 주요 뉴스를 요약해보고, 개인 맞춤형 뉴스 추천을 받을 수 있으며, 궁금한 점은 챗봇을 통해 자연어로 질문해 바로 해답을 얻을 수 있습니다.

넘치는 뉴스 속에서 정말 필요한 정보만 빠르게 파악하고 싶은 사용자들을 위한, 똑똑하고 효율적인 뉴스 소비 경험을 제공합니다.

<br>

# 📣 Medium
> 🔎 [요즘N Medium](https://medium.com/@dongan0618/%EC%8B%A4%EC%8B%9C%EA%B0%84-%EB%89%B4%EC%8A%A4-ai-%EC%9A%94%EC%95%BD-%EA%B4%80%EC%8B%AC-%ED%82%A4%EC%9B%8C%EB%93%9C%EA%B9%8C%EC%A7%80-%ED%95%9C-%EB%B2%88%EC%97%90-%EC%9A%94%EC%A6%98n-2025-siliconvalley-summer-bootcamp-6d221755fa81) &nbsp;
<br>

# 🎥 Demo
### 초기 설정 (Initial Setting)
>사용자는 관심 언론사, 관심 카테고리, 관심 키워드를 자신의 관심도에 맞게 설정할 수 있습니다.<BR>
>음성 지원을 위한 보이스 타입도 선택 가능하며, 키워드는 단순 단어뿐만 아니라 문장 단위로도 등록할 수 있습니다.<BR>
>(예: ‘비트코인 관련 전망’, ‘대통령 연설’ 등)
<img src="" />
<br>

### 메인 페이지 (Main Page)
>실시간 뉴스, 오늘의 뉴스, 키워드별 뉴스로 구성되어 있습니다.<BR>
>실시간 뉴스와 키워드별 뉴스는 썸네일 형태로 제공되며, 오늘의 뉴스는 사용자가 설정한 관심 카테고리별로 분류되어 보여집니다.

<img src=""/>
<br>

### 상세 페이지 (Detail Page)
>원하는 기사를 선택하면 해당 기사의 제목, 이미지, 발행 시간 등을 확인할 수 있습니다. <BR>
>요약된 기사 내용을 텍스트로 읽거나 음성으로 청취할 수 있으며, 챗봇 버튼을 통해 추가적인 대화도 가능합니다.

<img src=""/>
<br>

### 챗봇 페이지 (Chatbot Page)
>사용자가 읽고 있는 기사의 내용을 AI가 사전에 학습하여, 해당 기사에 대한 질문에 실시간으로 답변을 제공합니다.

<img src=""/>
<br>

### 키워드 페이지 (Keyword Page)
>사용자가 설정한 관심 언론사와 카테고리를 기반으로 등록한 관심 키워드와 가장 관련성 높은 뉴스 기사들을 비교·분석해 큐레이션하여 키워드 간 유사도 분석을 통해 맞춤형 기사를 제공합니다.
<img src=""/>
<br>

### 히스토리 페이지 (History Page)
>사용자가 이전에 읽었던 기사들을 한눈에 확인할 수 있어, 뉴스 소비 이력을 쉽게 돌아볼 수 있습니다.

<img src=""/>
<br>

### 즐겨찾기 페이지 (Bookmark  Page)
>관심 있는 기사를 즐겨찾기에 추가해두면, 언제든지 다시 찾아보고 읽을 수 있습니다.

<img src=""/>
<br>


## 💻 System Architechture
<img src="https://github.com/user-attachments/assets/a11d284a-cd21-4480-b196-8257b16b066a" />

## 💾 ERD
<p align="center">
 <img src="https://github.com/user-attachments/assets/f80c806d-e945-4c11-ac31-4fca1a04e018" />
</p>

## 🛠️ Tech stack

| Area | Tech Stack |
|:---:|:---|
| **Frontend** | <img src="https://img.shields.io/badge/flutter-02569B?style=for-the-badge&logo=flutter&logoColor=white" /> |
| **Backend** | <img src="https://img.shields.io/badge/fastapi-009688?style=for-the-badge&logo=fastapi&logoColor=white" /> <img src="https://img.shields.io/badge/uvicorn-333333?style=for-the-badge&logo=uvicorn&logoColor=white" /> <img src="https://img.shields.io/badge/nginx-009639?style=for-the-badge&logo=nginx&logoColor=white" /> |
| **Task Queue** | <img src="https://img.shields.io/badge/celery-3782A6?style=for-the-badge&logo=celery&logoColor=white" /> <img src="https://img.shields.io/badge/redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" /> <img src="https://img.shields.io/badge/rabbitmq-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white" /> |
| **AI / NLP** | <img src="https://img.shields.io/badge/openai-412991?style=for-the-badge&logo=openai&logoColor=white" /> <img src="https://img.shields.io/badge/google%20speech%20api-4285F4?style=for-the-badge&logo=google&logoColor=white" /> |
| **Search / Indexing** | <img src="https://img.shields.io/badge/opensearch-005EB8?style=for-the-badge&logo=opensearch&logoColor=white" /> |
| **Database / Storage** | <img src="https://img.shields.io/badge/postgresql-336791?style=for-the-badge&logo=postgresql&logoColor=white" /> <img src="https://img.shields.io/badge/google%20cloud%20storage-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white" /> |
| **DevOps / Infra** | <img src="https://img.shields.io/badge/docker%20compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" /> <img src="https://img.shields.io/badge/gcp-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white" /> |
| **Monitoring** | <img src="https://img.shields.io/badge/prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white" /> <img src="https://img.shields.io/badge/grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white" /> <img src="https://img.shields.io/badge/cadvisor-2196F3?style=for-the-badge&logo=google&logoColor=white" /> |
| **CI / CD** | <img src="https://img.shields.io/badge/github%20actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" /> |





## ✨ API
 <img src="https://github.com/user-attachments/assets/18bf3223-635a-43fb-ac89-30da77914ef2" />
</p>
 <img src="https://github.com/user-attachments/assets/aa243090-b489-4063-997e-0de82cce72eb" />
</p>


# 📊 Monitoring

<h3 align="left">Prometheus & Grafana</h3>
<table>
    <tr>
        <th colspan="2">fastapi</th>
    </tr>
    <tr>
        <td><img src="" alt="Django"></td>
        <td><img src="" alt="Django2"></td>
    </tr>
    <tr>
    <tr>
        <th colspan="2">cAdvisor</th>
    </tr>
    <tr>
        <td><img src="" alt="cAdvisor2"></td>
    </tr>
    <tr>
        <th colspan="2"></th>
    </tr>
    <tr>
    </tr>
</table>


<br>

</div>

## 🚀 How to Start
#### 1. Clone The Repository

## 🧑‍🤝‍🧑Member
<table width="1000">
    <thead>
    </thead>
    <tbody>
    <tr>
        <th>Pictures</th>
         <td width="100" align="center">
            <a href="https://github.com/docodocod">
                <img src="https://github.com/user-attachments/assets/74a571ec-73b1-4a06-9362-a88e1623f50a" width="100" height="100">
            </a>
        </td>
        <td width="100" align="center">
             <a href="https://github.com/inu-ung">
                <img src="https://github.com/user-attachments/assets/a31b02fa-7b47-468d-a852-cabb1fa1ae2b" width="100" height="100">
            </a>
        </td>
        <td width="100" align="center">
             <a href="https://github.com/Minho2003">
                <img src="https://github.com/user-attachments/assets/9ab2bf6f-39c1-4e1f-873a-6546f2205af4" width="100" height="100">
            </a>
        </td>
        <td width="100" align="center">
             <a href="https://github.com/haeunmochi">
                <img src="https://github.com/user-attachments/assets/67c1049c-82e2-44d2-beee-bde12c0e7c0b" width="100" height="100">
            </a>
        </td>
        <td width="100" align="center">
             <a href="https://github.com/kai8582">
                <img src="" width="100" height="100">
            </a>
        </td>
    </tr>
    <tr>
        <th>Name</th>
        <td width="100" align="center">김동안</td>
        <td width="100" align="center">정철웅</td>
        <td width="100" align="center">최민호</td>
        <td width="100" align="center">김하은</td>
        <td width="100" align="center">김주호</td>
    </tr>
    <tr>
        <th>Position</th>
        <td width="150" align="center">
            Leader<br>
            Backend<br>
            DevOps<br>
        </td>
        <td width="150" align="center">
            Fullstack<br>
            DevOps<br>
        </td>
        <td width="150" align="center">
            Fullstack<br>
            DevOps<br>
        </td>
        <td width="150" align="center">
            Frontend<br>
            Design<br>
        </td>
        <td width="150" align="center">
            Frontend<br>
            Design<br>
        </td>
    </tr>
    <tr>
        <th>GitHub</th>
        <td width="100" align="center">
            <a href="https://github.com/docodocod">
                <img src="https://img.shields.io/badge/GitHub-docodocod-black?style=for-the-badge&logo=github"/>
            </a>
        </td>
        <td width="100" align="center">
            <a href="https://github.com/inu-ung">
                <img src="https://img.shields.io/badge/GitHub-inu--ung-black?style=for-the-badge&logo=github"/>
            </a>
        </td>
        <td width="100" align="center">
            <a href="https://github.com/Minho2003">
                <img src="https://img.shields.io/badge/GitHub-Minho2003-black?style=for-the-badge&logo=github"/>
            </a>
        </td>
        <td width="100" align="center">
            <a href="https://github.com/ehdgusdl">
                <img src="https://img.shields.io/badge/GitHub-ehdgusdl-black?style=for-the-badge&logo=github"/>
            </a>
        </td>
        <td width="100" align="center">
            <a href="https://github.com/kai8582">
                <img src="https://img.shields.io/badge/GitHub-kai8582-black?style=for-the-badge&logo=github"/>
            </a>
        </td>
    </tr>
    </tbody>
</table>
