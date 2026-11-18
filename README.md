# Finding Bird!
Windows에서 Python 3.10 이상과 VS Code의 Microsoft Python 및 Python Debugger 확장을 설치합니다. 압축을 풀고 app.py가 있는 폴더를 VS Code에서 열어 F5를 누릅니다. 터미널에서는 py app.py로 실행할 수 있습니다. 첫 실행에서 실제 새 사진 데이터를 준비합니다. 인터넷과 약 3GB의 여유 공간이 필요합니다. 준비가 끝나면 브라우저에서 200종 사진 대결을 시작합니다.
## 게임
먼저 부위와 색을 직접 입력해 물어보고 도감에서 정답을 선택합니다. 예를 들어 “배가 노란색입니까?” 뒤에 “등도 노란색입니까?”을 물을 수 있습니다. 단서 사전에서 CUB 외형 속성 312개를 검색할 수 있습니다. 서식지·물갈퀴·다부진 체형은 아래 출처에서 확인한 일부 종에만 별도 정보를 제공합니다. 다음 라운드에서는 사진을 보며 삐오의 질문에 “그렇습니다”, “아닙니다”, “잘 모르겠습니다” 중 하나로 답합니다. 질문과 추측은 각각 1회, 도감 열람은 무료입니다. 20회 이내 성공을 우선하며 두 사람 모두 성공하면 적게 사용한 쪽이 이깁니다. 동률이면 재경기 버튼으로 새 경기를 시작합니다.
## 파일
app.py는 로컬 게임 서버, 채팅 규칙과 AI 질문 전략입니다. static은 브라우저 화면 및 그림, setup_cub.py는 데이터 준비 코드입니다. 서버를 끄거나 페이지를 새로 열면 새 경기를 시작합니다.
원본 https://data.caltech.edu/records/65de6-vp158
속성 이름 https://huggingface.co/datasets/pawlo2013/CUB/blob/main/attributes.txt

생태 단서 출처
- https://www.fws.gov/rivers/sites/default/files/documents/2025-11/laysan-albatross-lesson-booklet.pdf
- https://www.allaboutbirds.org/guide/Eared_Grebe/id
- https://www.allaboutbirds.org/guide/Western_Grebe/lifehistory
- https://www.allaboutbirds.org/guide/Horned_Puffin/id
