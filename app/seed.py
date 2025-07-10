import random
from datetime import datetime, timedelta, timezone
from random import choice, randint, sample
from random import seed as rand_seed

from faker import Faker
from neomodel import db
from passlib.hash import pbkdf2_sha256

from app.models.comment import Comment
from app.models.post import Post
from app.models.user import Skill, User

faker = Faker()
Faker.seed(0)
rand_seed(0)


TEST_USER_PROFILE_IMAGE = "https://res.cloudinary.com/dlqavunid/image/upload/v1748465766/OmarSwailamPic_jsbpbq.jpg"
TEST_USER_POST_IMAGES = [
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465744/game-presentation-slider-image-3_twj274.jpg",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465746/Screenshot_70_ypj7bk.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465745/Screenshot_166_jgonmp.png",
]


PROFILE_IMAGES = [
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465766/ChatGPT_Image_May_22_2025_11_26_13_PM_fy9vui.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465764/ChatGPT_Image_May_22_2025_11_27_54_PM_pys9je.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465764/ChatGPT_Image_May_22_2025_11_27_04_PM_uztgvx.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465764/ChatGPT_Image_May_22_2025_11_28_45_PM_aquqwc.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465763/ChatGPT_Image_May_22_2025_11_29_39_PM_wguk0n.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465762/ChatGPT_Image_May_22_2025_11_30_38_PM_tgrfkh.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465760/ChatGPT_Image_May_22_2025_11_31_31_PM_vkifr7.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465760/ChatGPT_Image_May_22_2025_11_32_50_PM_fcv5ty.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465759/ChatGPT_Image_May_22_2025_11_38_49_PM_dlkkzw.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465759/ChatGPT_Image_May_22_2025_11_39_41_PM_emyxj8.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465758/ChatGPT_Image_May_22_2025_11_48_41_PM_xcrjdp.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465757/ChatGPT_Image_May_22_2025_11_49_42_PM_zrh0zo.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465757/ChatGPT_Image_May_22_2025_11_50_40_PM_qsvog9.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465750/ChatGPT_Image_May_22_2025_11_59_36_PM_dh25kx.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465747/ChatGPT_Image_May_23_2025_12_01_06_AM_rnszrk.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465756/istockphoto-1437816897-612x612_ofkcfo.jpg",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465756/premium_photo-1689568126014-06fea9d5d341_jfk5yk.jpg",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465755/photo-1438761681033-6461ffad8d80_ybtmwg.jpg",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465753/istockphoto-1317804578-612x612_olngjn.jpg",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465752/head-shot-portrait-close-smiling-600nw-1714666150_sulxpr.webp",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465751/istockphoto-1388253782-612x612_phfm33.jpg",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465751/istockphoto-1485546774-612x612_mlxokp.jpg",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465751/pretty-smiling-joyfully-female-with-fair-hair-dressed-casually-looking-with-satisfaction_176420-15187_tmi9uy.avif",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465751/premium_photo-1682096252599-e8536cd97d2b_r9192o.jpg",
]

POST_IMAGES = [
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465747/a1_qgzj0k.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465747/a2_ojyyof.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465746/Screenshot_12_pk2c5q.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465745/Screenshot_166_jgonmp.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465745/2_wovyrn.jpg",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465744/witcher_b6ssrd.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465746/Screenshot_70_ypj7bk.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465742/10-102053_assassins-creed-odyssey_tnfw1i.jpg",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465741/Screenshot_315_na4weq.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465739/190517103414-01-grumpy-cat-file-restricted_rgiskl.jpg",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465739/1920x_psimmc.jpg",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465739/stray_bs6gac.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465739/photomode_02102022_235615_jyd8sc.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465739/_106997902_gettyimages-611696954_fddnsb.jpg",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465738/photomode_03102022_000111_n8obnn.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465736/photomode_03102022_001544_wwoz0i.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465735/photomode_06102022_143016_lsbwag.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465734/sprider_warte1.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465734/photomode_07102022_123440_zosd33.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465734/photomode_14102022_130837_bwqael.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465732/buddy-photo-omxwwtNse3k-unsplash_a7cazm.jpg",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465732/Screenshot_160_pqhgdj.png",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465731/dasha-yukhymyuk-CA0cp1SFTXU-unsplash_rpnxf4.jpg",
    "https://res.cloudinary.com/dlqavunid/image/upload/v1748465731/annie-spratt-42JiiY4agyE-unsplash_fmyu9o.jpg",
]

SKILLS = [
    # Tech & Engineering
    "Python",
    "Django",
    "React",
    "Vue",
    "Neo4j",
    "FastAPI",
    "SQL",
    "PostgreSQL",
    "MongoDB",
    "Elasticsearch",
    "Kubernetes",
    "Docker",
    "AWS",
    "Azure",
    "Terraform",
    "CI/CD Pipelines",
    "TypeScript",
    "JavaScript",
    "Golang",
    "Rust",
    "C++",
    "Java",
    "Flutter",
    "iOS Development",
    "Android Development",
    # Design & Creative
    "Adobe Photoshop",
    "Figma",
    "UI/UX Design",
    "Graphic Design",
    "3D Modeling",
    "Animation",
    "Motion Graphics",
    "Illustration",
    "Copywriting",
    "Video Editing",
    "Photography",
    # Data & AI
    "Machine Learning",
    "Data Science",
    "Big Data",
    "TensorFlow",
    "PyTorch",
    "NLP",
    "Computer Vision",
    "Data Engineering",
    "Business Intelligence",
    "Data Visualization",
    "ETL Pipelines",
    "Power BI",
    "Tableau",
    "SAS",
    # Business & Marketing
    "Digital Marketing",
    "SEO",
    "SEM",
    "Content Marketing",
    "Social Media Strategy",
    "Brand Management",
    "CRM Systems",
    "Project Management",
    "Product Management",
    "Agile Methodologies",
    "Scrum",
    "Lean Startup",
    "Business Analysis",
    "Financial Modeling",
    "Risk Management",
    "Supply Chain Management",
    # Languages & Soft Skills
    "English (Fluent)",
    "Arabic (Native)",
    "French (Intermediate)",
    "Spanish (Fluent)",
    "Mandarin (Basic)",
    "German (Intermediate)",
    "Public Speaking",
    "Leadership",
    "Teamwork",
    "Conflict Resolution",
    "Negotiation",
    "Time Management",
    "Adaptability",
    # Science & Healthcare
    "Molecular Biology",
    "Bioinformatics",
    "Lab Techniques",
    "Clinical Research",
    "Pharmacology",
    "Biostatistics",
    "Medical Writing",
    "Healthcare Data Analysis",
    "Epidemiology",
    # Industry & Trades
    "Welding",
    "Carpentry",
    "Plumbing",
    "Electrical Systems",
    "CNC Machining",
    "Industrial Automation",
    "Mechanical Design",
    "Civil Engineering",
    "Structural Analysis",
    "CAD Drafting",
]


# def convert_drive_url(url: str, size: str) -> str:
#     file_id = url.split("/d/")[1].split("/")[0]
#     return f"https://drive.google.com/thumbnail?id={file_id}&sz={size}"


def random_date_after(start: datetime = None) -> datetime:
    now = datetime.now(timezone.utc)

    if start is None:
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    elif start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)

    if start > now:
        return now

    delta = now - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)


def random_date(start: datetime = None) -> datetime:
    now = datetime.now(timezone.utc)
    choice = random.choice(["today", "yesterday", "random"])
    if choice == "today":
        return now
    elif choice == "yesterday":
        return now - timedelta(days=1)
    else:
        return random_date_after(start)


def wipe_database():
    db.cypher_query("MATCH (n) DETACH DELETE n")


def seed():
    wipe_database()

    print("seeding database...")
    print("creating users and posts...")
    users = []
    for img_url in PROFILE_IMAGES:
        user = User(
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            email=faker.unique.email(),
            title=f"{faker.job()} @ {faker.company()}",
            password=pbkdf2_sha256.hash("defaultpassword123"),
            profile_image=img_url,
        ).save()
        users.append(user)

        user_skills = sample(SKILLS, k=faker.random_int(min=1, max=10))
        for skill_name in user_skills:
            skill = Skill.nodes.first_or_none(name=skill_name)
            if not skill:
                skill = Skill(name=skill_name).save()
            user.skills.connect(skill)

    for i, user in enumerate(users):
        follow_count = randint(3, 6)
        possible_targets = [u for u in users if u != user]
        targets = sample(
            possible_targets, min(follow_count, len(possible_targets))
        )
        for target in targets:
            user.follow(target)

    for i, user in enumerate(users):
        for _ in range(3):
            post = Post(
                text=faker.paragraph(), images=[], created_at=random_date()
            ).save()
            post.created_by.connect(user)

        post_with_image = Post(
            text=faker.paragraph(),
            images=[POST_IMAGES[i]],
            created_at=random_date(),
        ).save()
        post_with_image.created_by.connect(user)

    test_user = User.find_by_email("test@test.com")
    if not test_user:
        test_user = User(
            first_name="Omar",
            last_name="Swailam",
            email="test@test.com",
            title="Software Engineer",
            password=pbkdf2_sha256.hash("123456789"),
            profile_image=TEST_USER_PROFILE_IMAGE,
        ).save()
        print("test user created: test@test.com / 123456789")

        test_user_skills = sample(SKILLS, k=faker.random_int(min=10, max=20))
        for skill_name in test_user_skills:
            skill = Skill.nodes.first_or_none(name=skill_name)
            if not skill:
                skill = Skill(name=skill_name).save()
            test_user.skills.connect(skill)

    test_user_targets = sample([u for u in users if u != test_user], 5)
    for target in test_user_targets:
        test_user.follow(target)

    test_user_followers = sample([u for u in users if u != test_user], 15)
    for follower in test_user_followers:
        follower.follow(test_user)

    for _ in range(20):
        Post(
            text=faker.paragraph(), images=[], created_at=random_date()
        ).save().created_by.connect(test_user)

    Post(
        text="Those are some shots I captured from playing Red Dead Redemption 2, what do you think ?",
        images=TEST_USER_POST_IMAGES,
        created_at=datetime.now(timezone.utc),
    ).save().created_by.connect(test_user)

    print("users and posts created.")
    print("creating comments and likes...")
    all_posts = Post.nodes.all()
    for post in all_posts:
        comment_count = randint(2, 4)
        for _ in range(comment_count):
            commenter = choice(users)
            comment = Comment(
                text=faker.sentence(), created_at=random_date(post.created_at)
            ).save()
            comment.created_by.connect(commenter)
            comment.on_post.connect(post)

            if randint(0, 1):
                reply_count = randint(1, 2)
                for _ in range(reply_count):
                    replier = choice(users)
                    reply = Comment(
                        text=faker.sentence(),
                        created_at=random_date(comment.created_at),
                    ).save()
                    reply.created_by.connect(replier)
                    reply.reply_to.connect(comment)

    test_user_posts_data = User.get_user_posts(
        test_user.uuid, test_user.uuid, page=1, page_size=1000
    )
    test_user_posts = test_user_posts_data["results"]
    for post in test_user_posts:
        comment_count = randint(2, 4)
        for _ in range(comment_count):
            commenter = choice(users)
            comment = Comment(
                text=faker.sentence(), created_at=random_date(post.created_at)
            ).save()
            comment.created_by.connect(commenter)
            comment.on_post.connect(post)

            reply_count = randint(0, 3)
            for _ in range(reply_count):
                replier = choice(users)
                reply = Comment(
                    text=faker.sentence(),
                    created_at=random_date(comment.created_at),
                ).save()
                reply.created_by.connect(replier)
                reply.reply_to.connect(comment)

                likers = sample(users, randint(0, 2)) 
                for liker in likers:
                    liker.likes_comment.connect(reply)

    for post in all_posts:
        likers = sample(users, randint(2, 7))
        for liker in likers:
            liker.likes.connect(post)

    for post in test_user_posts:
        likers = sample(users, randint(5, 15))
        for liker in likers:
            liker.likes.connect(post)

    all_comments = Comment.nodes.all()
    for comment in all_comments:
        likers = sample(users, randint(1, 4))
        for liker in likers:
            liker.likes_comment.connect(comment)

    print("comments and likes created")
    print("seeding complete.")
