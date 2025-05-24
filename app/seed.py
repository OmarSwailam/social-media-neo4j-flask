from random import choice, randint, sample
from random import seed as rand_seed

from faker import Faker
from neomodel import db
from passlib.hash import pbkdf2_sha256

from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User

faker = Faker()
Faker.seed(0)
rand_seed(0)

TEST_USER_PROFILE_IMAGE = "https://drive.google.com/file/d/1jcMX3Hh8dgfsQ0F7G0WyVtr9ZwSNYz9O/view?usp=sharing"
TEST_USER_POST_IMAGE = "https://drive.google.com/file/d/14xradvlNfJr4NfNWG7yKlD8AkA9UJP5G/view?usp=drive_link"

PROFILE_IMAGES = [
    "https://drive.google.com/file/d/1hUMc1cGR0VaUArcEzfo5F5ktm-cgUW6D/view?usp=drive_link",
    "https://drive.google.com/file/d/1KEkc92Ufx7e9T7T8F0ZzoCGv8h3AUxop/view?usp=drive_link",
    "https://drive.google.com/file/d/1gO0qKU8q5c7rGqZ068U1L5k4FT5-LdyX/view?usp=drive_link",
    "https://drive.google.com/file/d/1YtiRI1jVrkApjB8b21Us7Y9nTFP16hmq/view?usp=drive_link",
    "https://drive.google.com/file/d/1PBTlclVw2UAHdqkVuK2O-rbQ0pkoIfNx/view?usp=drive_link",
    "https://drive.google.com/file/d/1IcGmx06EyzEFHxTz3MQWT74Fys8Ix27w/view?usp=drive_link",
    "https://drive.google.com/file/d/1i_qPtc7eNvGauzha3KGSONguG_chK9Fk/view?usp=drive_link",
    "https://drive.google.com/file/d/134JXO8TQHXSMyYQnJrDcZIYJ8_Tv-5ZL/view?usp=drive_link",
    "https://drive.google.com/file/d/1XOWozhJkNUZy7Dh4iQq4CjCuXvfcRoXu/view?usp=drive_link",
    "https://drive.google.com/file/d/1n4l2chubu-LLVtOpHfaCQ3XKb8oQacoD/view?usp=drive_link",
    "https://drive.google.com/file/d/1p4CGV7YTICuP_RTDSaTK9e3c9QjzMSAX/view?usp=drive_link",
    "https://drive.google.com/file/d/1ySSJ62VJV8CJ-9fMnFDXF2tz6wxm26QB/view?usp=drive_link",
    "https://drive.google.com/file/d/1tzYAp8K7XfHF-5rnA952_ce9HBXbuq0q/view?usp=drive_link",
    "https://drive.google.com/file/d/1B9miOrRZfsXabFI059epj8weYDD1CK4c/view?usp=drive_link",
    "https://drive.google.com/file/d/17aKRMhdY5oPoQV9h3a8LHsxSHOM9rSaw/view?usp=drive_link",
    "https://drive.google.com/file/d/137AIe_-pmes_ZWOpop9ygKMW2j17OFOA/view?usp=drive_link",
    "https://drive.google.com/file/d/17iMjh7DspQTNXcm8Wes3DMMcptTvJ5iu/view?usp=drive_link",
    "https://drive.google.com/file/d/1-6lwUHez3Ob9m5F38lEuuhGAH-f6OQ7Z/view?usp=drive_link",
    "https://drive.google.com/file/d/167U8oH2CErsoDwDccsVPVvOM92Eg6tPW/view?usp=drive_link",
    "https://drive.google.com/file/d/1vTRkPmXpyk2RGajX-3Vjvho3VQtFA6aw/view?usp=drive_link",
    "https://drive.google.com/file/d/1762GFNWBQQRgIHxHSGRzwOQpK2SR1pFs/view?usp=drive_link",
    "https://drive.google.com/file/d/1dzjyKmCkg6IRkYkw-HVxtb_9PXylhByX/view?usp=drive_link",
    "https://drive.google.com/file/d/1YOppOEcECwozgsanx7HY5BVaSSsN9e23/view?usp=drive_link",
    "https://drive.google.com/file/d/14GtcovfA-Az77TwSW9b2sqHESSf_zZ-1/view?usp=drive_link",
]

POST_IMAGES = [
    "https://drive.google.com/file/d/1wNAUFFDDIIX3gfFYgub8lelsWYHvXkKp/view?usp=drive_link",
    "https://drive.google.com/file/d/17gbs4aiMCbKa5muyMDdQVnoaLkoBFBmL/view?usp=drive_link",
    "https://drive.google.com/file/d/1ILdNvUuph2k0-sgGpTb-xf8klwGJq0l1/view?usp=drive_link",
    "https://drive.google.com/file/d/1eR0J6cD3ATGK02nfFRui04tB32qipnhM/view?usp=drive_link",
    "https://drive.google.com/file/d/1TNvPdKDOaiEVrUKAbb3wY4i7CdrDmG-q/view?usp=drive_link",
    "https://drive.google.com/file/d/1PRm9UP9B3OSeOUxDnjxPjwTfP6WADUHt/view?usp=drive_link",
    "https://drive.google.com/file/d/1ASpkOlrYK7c17OJ5dQVQkT4k2qtzGiM7/view?usp=drive_link",
    "https://drive.google.com/file/d/1As2Cyb-uk4LHMRTjJ_mmQveARbc3qD59/view?usp=drive_link",
    "https://drive.google.com/file/d/1FjxCzUv5FKGcHuI4_UQS9gt-68t5AWfV/view?usp=drive_link",
    "https://drive.google.com/file/d/1Ly-U4Qw0FwUVvX6XwwBJWHj85TafqsQD/view?usp=drive_link",
    "https://drive.google.com/file/d/1ZBSI2v8JPtqQb5u3TV8pJlHdouaOWGXC/view?usp=drive_link",
    "https://drive.google.com/file/d/1pz6xyrvxKiMzixXWfk_mFfODqrWEJFKq/view?usp=drive_link",
    "https://drive.google.com/file/d/1PlnolqjswtnRn2sNiKs8XqGpohTfAlJ9/view?usp=drive_link",
    "https://drive.google.com/file/d/1CC5FMINA0Lpw5refFEaKCxJYyl3X71_R/view?usp=drive_link",
    "https://drive.google.com/file/d/1mxtyZhotIfTfTmFQlfityRD6I8aM-QbF/view?usp=drive_link",
    "https://drive.google.com/file/d/1jXeX-kmbI-ue-yhCBoPzXBX-tziiIobm/view?usp=drive_link",
    "https://drive.google.com/file/d/1tpa7EP7pKFE0n_a1FhTw1v5ANgr3RGrk/view?usp=drive_link",
    "https://drive.google.com/file/d/1xV6S8rx3U8n7Nf_Lrwks13o6AJi-ooiU/view?usp=drive_link",
    "https://drive.google.com/file/d/1CKVDjVaiuCQO7sCu71P32FFPGe5zHhZu/view?usp=drive_link",
    "https://drive.google.com/file/d/1kPhyw1A323_0XeGO49H2CG7b1y1XuuhC/view?usp=drive_link",
    "https://drive.google.com/file/d/1_1upHn3M5OTX77O0iL2b1gM2dpA_FTjw/view?usp=drive_link",
    "https://drive.google.com/file/d/1hSK9k_3M85jUcuUbEe2TnJzvARN-uU_U/view?usp=drive_link",
    "https://drive.google.com/file/d/1KCwZfp3jAO55u8LVFidAUVJGzDELNeFE/view?usp=drive_link",
    "https://drive.google.com/file/d/1GRQfF9zwbS_E_AlW7N_CumqqKYsvxrOs/view?usp=drive_link",
]


def convert_drive_url(url: str) -> str:
    file_id = url.split("/d/")[1].split("/")[0]
    return f"https://drive.google.com/uc?export=view&id={file_id}"


def wipe_database():
    db.cypher_query("MATCH (n) DETACH DELETE n")


def seed():
    wipe_database()

    print("seeding data...")
    print("creating users and posts...")
    users = []
    for img_url in PROFILE_IMAGES:
        user = User(
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            email=faker.unique.email(),
            password=pbkdf2_sha256.hash("defaultpassword123"),
            profile_image=convert_drive_url(img_url),
        ).save()
        users.append(user)

    for i, user in enumerate(users):
        follow_count = randint(3, 6)
        possible_targets = [u for u in users if u != user]
        targets = sample(
            possible_targets, min(follow_count, len(possible_targets))
        )
        for target in targets:
            user.follow(target)

    for i, user in enumerate(users):
        post_with_image = Post(
            text=faker.paragraph(),
            images=[convert_drive_url(POST_IMAGES[i])],
        ).save()
        post_with_image.created_by.connect(user)

        for _ in range(2):
            post = Post(
                text=faker.paragraph(),
                images=[],
            ).save()
            post.created_by.connect(user)

    print("users and posts created.")
    test_user = User.find_by_email("test@test.com")
    if not test_user:
        test_user = User(
            first_name="Omar",
            last_name="Swailam",
            email="test@test.com",
            password=pbkdf2_sha256.hash("12345678"),
            profile_image=convert_drive_url(TEST_USER_PROFILE_IMAGE),
        ).save()
        print("test user created: test@test.com / 12345678")

    test_user_targets = sample([u for u in users if u != test_user], 5)
    for target in test_user_targets:
        test_user.follow(target)

    test_user_followers = sample([u for u in users if u != test_user], 15)
    for follower in test_user_followers:
        follower.follow(test_user)
        
    Post(
        text=faker.paragraph(),
        images=[convert_drive_url(TEST_USER_POST_IMAGE)],
    ).save().created_by.connect(test_user)

    for _ in range(2):
        Post(
            text=faker.paragraph(),
            images=[],
        ).save().created_by.connect(test_user)

    print("creating comments and likes...")
    all_posts = Post.nodes.all()
    for post in all_posts:
        comment_count = randint(2, 4)
        for _ in range(comment_count):
            commenter = choice(users)
            comment = Comment(text=faker.sentence()).save()
            comment.created_by.connect(commenter)
            comment.on_post.connect(post)

            if randint(0, 1):
                reply_count = randint(1, 2)
                for _ in range(reply_count):
                    replier = choice(users)
                    reply = Comment(text=faker.sentence()).save()
                    reply.created_by.connect(replier)
                    reply.reply_to.connect(comment)

    test_user_posts_data = User.get_user_posts(
        test_user.uuid, page=1, page_size=1000
    )
    test_user_posts = test_user_posts_data["results"]
    for post in test_user_posts:
        comment_count = randint(2, 4)
        for _ in range(comment_count):
            commenter = choice(users)
            comment = Comment(text=faker.sentence()).save()
            comment.created_by.connect(commenter)
            comment.on_post.connect(post)

            if randint(0, 1):
                reply_count = randint(1, 2)
                for _ in range(reply_count):
                    replier = choice(users)
                    reply = Comment(text=faker.sentence()).save()
                    reply.created_by.connect(replier)
                    reply.reply_to.connect(comment)


    for post in all_posts:
        likers = sample(users, randint(2, 6))
        for liker in likers:
            liker.likes.connect(post)

    for post in test_user_posts:
        likers = sample(users, randint(2, 6))
        for liker in likers:
            liker.likes.connect(post)

    all_comments = Comment.nodes.all()
    for comment in all_comments:
        likers = sample(users, randint(1, 4))
        for liker in likers:
            liker.likes_comment.connect(comment)

    print("comments and likes created")   
    print("seeding complete.")
