"""
Trip For U - Flask Backend Server
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
else:
    gemini_model = None
    print("⚠️  Warning: GEMINI_API_KEY not found. AI features will be disabled.")

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'tripforu.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ===== Database Models =====

class Activity(db.Model):
    """활동/장소 데이터"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # food, sight, shopping, cafe
    duration = db.Column(db.Integer, nullable=False)  # 분 단위
    description = db.Column(db.Text)
    tags = db.Column(db.String(500))  # JSON string
    indoor = db.Column(db.Boolean, default=False)
    cost = db.Column(db.String(100))
    address = db.Column(db.String(300))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'duration': self.duration,
            'description': self.description,
            'tags': self.tags.split(',') if self.tags else [],
            'indoor': self.indoor,
            'footer': self.cost,
            'address': self.address,
            'lat': self.lat,
            'lng': self.lng
        }


class Trip(db.Model):
    """여행 일정"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100))
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    transport = db.Column(db.String(50))
    preferences = db.Column(db.Text)  # JSON string
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'city': self.city,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'transport': self.transport,
            'preferences': self.preferences,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Itinerary(db.Model):
    """일정 상세 (여행의 각 활동)"""
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3...
    order_number = db.Column(db.Integer, nullable=False)  # 하루 내 순서
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))

    activity = db.relationship('Activity', backref='itineraries')

    def to_dict(self):
        activity_dict = self.activity.to_dict()
        activity_dict.update({
            'itinerary_id': self.id,
            'day_number': self.day_number,
            'order_number': self.order_number,
            'start_time': self.start_time,
            'end_time': self.end_time
        })
        return activity_dict


# ===== API Routes =====

@app.route('/')
def index():
    """메인 페이지"""
    return send_from_directory('.', 'index.html')


@app.route('/api/activities', methods=['GET'])
def get_activities():
    """모든 활동 조회"""
    category = request.args.get('category')
    indoor = request.args.get('indoor')

    query = Activity.query

    if category:
        query = query.filter_by(category=category)
    if indoor is not None:
        query = query.filter_by(indoor=indoor.lower() == 'true')

    activities = query.all()
    return jsonify([activity.to_dict() for activity in activities])


@app.route('/api/activities', methods=['POST'])
def create_activity():
    """새 활동 생성"""
    data = request.json

    activity = Activity(
        title=data['title'],
        category=data['category'],
        duration=data['duration'],
        description=data.get('description', ''),
        tags=','.join(data.get('tags', [])),
        indoor=data.get('indoor', False),
        cost=data.get('cost', ''),
        address=data.get('address', ''),
        lat=data.get('lat'),
        lng=data.get('lng')
    )

    db.session.add(activity)
    db.session.commit()

    return jsonify(activity.to_dict()), 201


@app.route('/api/trips', methods=['GET'])
def get_trips():
    """모든 여행 조회"""
    trips = Trip.query.order_by(Trip.created_at.desc()).all()
    return jsonify([trip.to_dict() for trip in trips])


@app.route('/api/trips', methods=['POST'])
def create_trip():
    """새 여행 생성"""
    data = request.json

    trip = Trip(
        title=data['title'],
        city=data['city'],
        start_date=data['start_date'],
        end_date=data['end_date'],
        start_time=data.get('start_time', '09:00'),
        end_time=data.get('end_time', '18:00'),
        transport=data.get('transport', '자차'),
        preferences=data.get('preferences', ''),
        notes=data.get('notes', '')
    )

    db.session.add(trip)
    db.session.commit()

    return jsonify(trip.to_dict()), 201


@app.route('/api/trips/<int:trip_id>', methods=['GET'])
def get_trip(trip_id):
    """특정 여행 조회"""
    trip = Trip.query.get_or_404(trip_id)
    return jsonify(trip.to_dict())


@app.route('/api/trips/<int:trip_id>', methods=['PUT'])
def update_trip(trip_id):
    """여행 수정"""
    trip = Trip.query.get_or_404(trip_id)
    data = request.json

    for key, value in data.items():
        if hasattr(trip, key):
            setattr(trip, key, value)

    db.session.commit()
    return jsonify(trip.to_dict())


@app.route('/api/trips/<int:trip_id>', methods=['DELETE'])
def delete_trip(trip_id):
    """여행 삭제"""
    trip = Trip.query.get_or_404(trip_id)

    # 관련 일정도 삭제
    Itinerary.query.filter_by(trip_id=trip_id).delete()

    db.session.delete(trip)
    db.session.commit()

    return jsonify({'message': 'Trip deleted successfully'}), 200


@app.route('/api/trips/<int:trip_id>/itinerary', methods=['GET'])
def get_itinerary(trip_id):
    """특정 여행의 일정 조회"""
    itineraries = Itinerary.query.filter_by(trip_id=trip_id).order_by(
        Itinerary.day_number, Itinerary.order_number
    ).all()

    # 날짜별로 그룹화
    days = {}
    for itinerary in itineraries:
        day = itinerary.day_number
        if day not in days:
            days[day] = []
        days[day].append(itinerary.to_dict())

    return jsonify(days)


@app.route('/api/trips/<int:trip_id>/itinerary', methods=['POST'])
def create_itinerary(trip_id):
    """일정에 활동 추가"""
    data = request.json

    itinerary = Itinerary(
        trip_id=trip_id,
        activity_id=data['activity_id'],
        day_number=data['day_number'],
        order_number=data['order_number'],
        start_time=data.get('start_time'),
        end_time=data.get('end_time')
    )

    db.session.add(itinerary)
    db.session.commit()

    return jsonify(itinerary.to_dict()), 201


@app.route('/api/generate-itinerary', methods=['POST'])
def generate_itinerary():
    """AI 기반 일정 생성 (알고리즘)"""
    data = request.json

    preferences = data.get('preferences', {})
    days_count = data.get('days', 3)
    weather = data.get('weather', 'sunny')

    # 활동 가져오기
    query = Activity.query

    # 날씨가 비일 경우 실내 활동만
    if weather == 'rainy':
        query = query.filter_by(indoor=True)

    all_activities = query.all()

    # 가중치 기반 점수 계산
    scored_activities = []
    for activity in all_activities:
        weight = preferences.get(activity.category, 25)
        score = weight * (1 + (0.5 if activity.indoor else 0))
        scored_activities.append({
            'activity': activity.to_dict(),
            'score': score
        })

    # 점수순 정렬
    scored_activities.sort(key=lambda x: x['score'], reverse=True)

    # 날짜별 분배
    days = [[] for _ in range(days_count)]
    activities_per_day = len(scored_activities) // days_count

    for i, item in enumerate(scored_activities[:days_count * 5]):  # 최대 5개씩
        day_index = i % days_count
        days[day_index].append(item['activity'])

    return jsonify({'days': days})


@app.route('/api/generate-itinerary-ai', methods=['POST'])
def generate_itinerary_ai():
    """Gemini AI 기반 일정 생성"""
    if not gemini_model:
        return jsonify({'error': 'Gemini API가 설정되지 않았습니다. GEMINI_API_KEY를 .env 파일에 추가해주세요.'}), 503

    data = request.json

    # 사용자 입력 데이터
    departure = data.get('departure', '대전')
    destination = data.get('destination', '서울')
    start_date = data.get('start_date', '2025-11-17')
    end_date = data.get('end_date', '2025-11-19')
    start_time = data.get('start_time', '09:00')
    end_time = data.get('end_time', '18:00')
    transport = data.get('transport', '자차')
    preferences = data.get('preferences', {})
    interests = data.get('interests', '')
    notes = data.get('notes', '')

    # Gemini 프롬프트 생성
    prompt = f"""
당신은 전문 여행 플래너입니다. 다음 정보를 바탕으로 상세한 여행 일정을 JSON 형식으로 생성해주세요.

**여행 정보:**
- 출발지: {departure}
- 도착지: {destination}
- 여행 기간: {start_date} ~ {end_date}
- 하루 활동 시간: {start_time} ~ {end_time}
- 이동 수단: {transport}
- 취향 비중: 맛집 {preferences.get('food', 25)}%, 관광 {preferences.get('sight', 25)}%, 쇼핑 {preferences.get('shopping', 25)}%, 카페/휴식 {preferences.get('cafe', 25)}%
- 관심사: {interests if interests else '없음'}
- 추가 요청사항: {notes if notes else '없음'}

**요구사항:**
1. 취향 비중에 따라 활동을 분배하세요 (맛집이 높으면 맛집 많이, 관광이 높으면 관광지 많이)
2. 실제로 존재하는 {destination}의 유명한 장소들을 포함하세요
3. 이동 시간과 거리를 고려하여 효율적으로 배치하세요
4. 각 활동은 현실적인 소요 시간을 가져야 합니다
5. 날씨, 피로도, 시간대(식사 시간 등)를 고려하세요

**출력 형식 (반드시 유효한 JSON으로만 응답):**
{{
  "days": [
    [
      {{
        "title": "활동명",
        "category": "food|sight|shopping|cafe",
        "duration": 60,
        "description": "상세 설명",
        "tags": ["#태그1", "#태그2", "#태그3"],
        "indoor": true,
        "footer": "예상 비용: 1인당 15,000원"
      }}
    ]
  ]
}}

반드시 JSON 형식으로만 응답하고, 다른 설명이나 텍스트는 포함하지 마세요.
"""

    try:
        # Gemini API 호출
        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()

        # JSON 파싱 시도
        # Gemini가 마크다운 코드 블록으로 감싸서 보낼 수 있으므로 처리
        if response_text.startswith('```json'):
            response_text = response_text[7:]  # ```json 제거
        if response_text.startswith('```'):
            response_text = response_text[3:]  # ``` 제거
        if response_text.endswith('```'):
            response_text = response_text[:-3]  # ``` 제거

        response_text = response_text.strip()

        # JSON 파싱
        result = json.loads(response_text)

        return jsonify(result)

    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        print(f"응답 텍스트: {response_text}")
        return jsonify({
            'error': 'AI 응답을 파싱할 수 없습니다.',
            'raw_response': response_text[:500]  # 처음 500자만
        }), 500

    except Exception as e:
        print(f"Gemini API 오류: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/seed-data', methods=['POST'])
def seed_data():
    """샘플 데이터 초기화"""
    # 기존 데이터 삭제
    db.drop_all()
    db.create_all()

    # 샘플 활동 추가
    sample_activities = [
        # 맛집
        Activity(title='봉피양 방이점', category='food', duration=60,
                description='봉피양 돼지갈비는 서울에서 유명한 맛집입니다.',
                tags='#가족친화,#돼지갈비,#주차_가능', indoor=True, cost='예상 비용: 1인당 15,000원'),
        Activity(title='광장시장 먹거리', category='food', duration=90,
                description='마약김밥, 빈대떡, 육회 등 다양한 전통 먹거리를 한 곳에서 즐길 수 있습니다.',
                tags='#전통시장,#길거리음식,#다양한메뉴', indoor=False, cost='예상 비용: 1인당 20,000원'),
        Activity(title='을지로 노가리골목', category='food', duration=120,
                description='서울의 레트로 감성이 물씬 풍기는 을지로에서 노가리와 함께 저녁을 즐겨보세요.',
                tags='#야경,#노가리,#분위기', indoor=False, cost='예상 비용: 1인당 25,000원'),

        # 관광
        Activity(title='롯데월드타워 & 서울스카이', category='sight', duration=150,
                description='서울의 랜드마크에서 탁 트인 전경을 감상하세요.',
                tags='#랜드마크,#관광명소,#전망대', indoor=True, cost='입장료: 성인 27,000원'),
        Activity(title='경복궁 & 국립민속박물관', category='sight', duration=90,
                description='조선 시대의 대표 궁궐인 경복궁을 둘러보며 한국의 역사를 체험해보세요.',
                tags='#역사,#문화,#한복체험', indoor=False, cost='입장료: 3,000원'),
        Activity(title='남산타워 야경 감상', category='sight', duration=90,
                description='케이블카를 타고 올라가 남산타워에서 서울 야경을 감상하세요.',
                tags='#야경,#데이트코스,#추억', indoor=False, cost='케이블카: 왕복 11,000원'),
        Activity(title='북촌 한옥마을 산책', category='sight', duration=90,
                description='전통 한옥이 잘 보존된 북촌에서 고즈넉한 산책을 즐겨보세요.',
                tags='#한옥,#포토존,#전통', indoor=False),

        # 쇼핑
        Activity(title='코엑스 스타필드 & 별마당 도서관', category='shopping', duration=120,
                description='아시아 최대 규모의 지하 쇼핑몰 코엑스에서 쇼핑과 함께 별마당 도서관을 방문해보세요.',
                tags='#쇼핑,#도서관,#실내', indoor=True, cost='무료 입장'),
        Activity(title='명동 쇼핑거리', category='shopping', duration=150,
                description='서울의 대표 쇼핑 거리 명동에서 쇼핑을 즐겨보세요.',
                tags='#쇼핑,#화장품,#패션', indoor=False),
        Activity(title='홍대 거리 쇼핑', category='shopping', duration=120,
                description='트렌디한 홍대에서 독특한 아이템들을 구경하고 구매해보세요.',
                tags='#젊은거리,#개성있는상품,#버스킹', indoor=False),

        # 카페
        Activity(title='성수동 카페 탐방', category='cafe', duration=60,
                description='힙한 성수동 카페거리에서 여유로운 커피 타임을 즐겨보세요.',
                tags='#카페,#디저트,#포토스팟', indoor=True, cost='예상 비용: 1인당 8,000원'),
        Activity(title='이태원 루프탑 카페', category='cafe', duration=90,
                description='이태원의 멋진 루프탑 카페에서 서울 시내를 내려다보며 커피를 즐기세요.',
                tags='#루프탑,#뷰맛집,#낭만', indoor=True, cost='예상 비용: 1인당 12,000원'),
        Activity(title='북촌 전통찻집', category='cafe', duration=60,
                description='한옥을 개조한 전통 찻집에서 조용한 시간을 보내세요.',
                tags='#전통차,#한옥카페,#힐링', indoor=True, cost='예상 비용: 1인당 10,000원'),
    ]

    for activity in sample_activities:
        db.session.add(activity)

    db.session.commit()

    return jsonify({'message': f'{len(sample_activities)} activities created successfully'}), 201


# ===== Initialize Database =====
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
