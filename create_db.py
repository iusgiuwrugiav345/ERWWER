import sqlite3
from database import db

# Initialize database
conn = sqlite3.connect("apps.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS apps (
    name TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    date_added TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()

# Add sample games
db.add_game(
    "minecraft",
    "https://dl.mcpelife.com/minecraft-ipa/1-21-71/Minecraft-v1.21.71.ipa",
    "game")
db.add_game(
    "gta vice city",
    "https://dl.iosvizor.net/grand-theft-auto-vice-city/GTA-Vice-City-v1-8.ipa",
    "game")
db.add_game(
    "stardew valley",
    "https://dl.iosvizor.net/stardew-valley/stardew-valley-v1.6.15.0-iosvizor.ipa",
    "game")
db.add_game(
    "gta san andreas",
    "https://dl.iosvizor.net/grand-theft-auto-san-andreas-2/GTA-San-Andreas-v2.2.20-iosvizor.ipa",
    "game")
db.add_game("getting over it",
            "https://dl.iosvizor.net/getting-over-it-v1.05.ipa", "game")
db.add_game(
    "human fall flat",
    "https://dl.iosvizor.net/human-fall-flat-plus/human-fall-flat-plus-v2.3.0-iosvizor.ipa",
    "game")
db.add_game(
    "nfs most wanted",
    "https://dl.iosvizor.net/need-for-speed-most-wanted/NFS-Most-Wanted-v1-1-3.ipa",
    "game")
db.add_game(
    "plague inc",
    "https://dl.iosvizor.net/Plague-Inc/Plague-Inc-v1.20.0-iosvizor.ipa",
    "game")
db.add_game(
    "real flight simulator",
    "https://dl.iosvizor.net/rfs-real-flight-simulator/rfs-real-flight-simulator-v2.5.9-iosvizor.ipa",
    "game")
db.add_game(
    "resident evil village",
    "https://dl.iosvizor.net/Resident-Evil-Village/Resident-Evil-Village-v1.1.6-iosvizor.ipa",
    "game")
db.add_game(
    "resident evil 4",
    "https://dl.iosvizor.net/Resident-Evil-4/Resident-Evil-4-v1.0.4-iosvizor.ipa",
    "game")
db.add_game(
    "goat simulator",
    "https://dl.iosvizor.net/goat-simulator/Goat-Simulator-v2.0.7-iosvizor.ipa",
    "game")
db.add_game("pou", "https://dl.iosvizor.net/pou/pou-v1.4.123.ipa", "game")
db.add_game(
    "geometry dash",
    "https://dl.iosvizor.net/geometry-dash/Geometry-Dash-v2.206-iosvizor.ipa",
    "game")
db.add_game(
    "bully",
    "https://dl.iosvizor.net/bully-anniversary-edition/Bully-Anniversary-Edition-v1-1.ipa",
    "game")
db.add_game(
    "mortal combat x",
    "https://dl.iosvizor.net/mortal-kombat-x/14179-Mortal-Kombat-X-v1-171.ipa",
    "game")
db.add_game("limbo", "https://dl.iosvizor.net/limbo/LIMBO-v1-1-15.ipa", "game")
db.add_game(
    "machinarium",
    "https://dl.iosvizor.net/machinarium/Machinarium-v3-0-9-iosvizor.com.ipa",
    "game")
db.add_game(
    "true skate",
    "https://dl.iosvizor.net/True%20Skate/True%20Skate-v1.5.91-iosvizor.ipa",
    "game")
db.add_game("forager", "https://dl.iosvizor.net/forager/Forager-1-0-5.ipa",
            "game")
db.add_game("day r", "https://dl.iosvizor.net/day-r/day-r-premium-v1.859.ipa",
            "game")
db.add_game(
    "motorsport manager 4",
    "https://dl.iosvizor.net/motorsport-manager-4/Motorsport-Manager-4-v2024.1.2-iosvizor.ipa",
    "game")
db.add_game(
    "wrc",
    "https://dl.iosvizor.net/wrc-the-official-game/WRC-The-Game-v1-0-01.ipa",
    "game")
db.add_game(
    "bridge constructor",
    "https://dl.iosvizor.net/bridge-constructor/bridge-constructor-v13.2-iosvizor.ipa",
    "game")
db.add_game("monopoly",
            "https://dl.iosvizor.net/monopoly/monopoly-v1-14-7.ipa", "game")
db.add_game("hitman sniper",
            "https://dl.iosvizor.net/hitman-sniper/hitman-sniper-v1-14.ipa",
            "game")
db.add_game(
    "atom rpg",
    "https://dl.iosvizor.net/atom-rpg/ATOM-RPG-v1.201.23-iosvizor.ipa", "game")
db.add_game(
    "guitar hero live",
    "https://dl.iosvizor.net/guitar-hero-live/Guitar-Hero-Live-v1-1-0.ipa",
    "game")
db.add_game(
    "max payne",
    "https://dl.iosvizor.net/max-payne-mobile/Max-Payne-Mobile-v2-0.ipa",
    "game")
db.add_game(
    "driving zone 2",
    "https://dl.iosvizor.net/driving-zone-2/Driving-Zone-2-v1-175.ipa", "game")
db.add_game(
    "rush rally origins",
    "https://dl.iosvizor.net/rush-rally-origins/Rush-Rally-Origins-v1-67.ipa",
    "game")
db.add_game("rush rally 3",
            "https://dl.iosvizor.net/rush-rally-3/Rush-Rally-3-v1.155.ipa",
            "game")
db.add_game("balatro",
            "https://dl.iosvizor.net/Balatro/Balatro-v1.1.7-iosvizor.ipa",
            "game")
db.add_game(
    "earn to die 2",
    "https://dl.iosvizor.net/earn-to-die-2/Earn-to-Die-2-v1.4.55-iosvizor.ipa",
    "game")
db.add_game(
    "fl studio mobile",
    "https://dl.iosvizor.net/fl-studio-mobile/fl-studio-mobile-v4.7.1-iosvizor.ipa",
    "app")
db.add_game("youtube plus",
            "https://dl.iosvizor.net/youtube/youtube-v20-12-4.ipa", "app")
db.add_game(
    "whatsapp messenger",
    "https://dl.iosvizor.net/whatsapp-messenger/whatsapp-messenger-mod-all-v25-6-2.ipa",
    "app")
db.add_game("video star",
            "https://dl.iosvizor.net/video-star/video-star-v14-0-7.ipa", "app")
db.add_game("esign", "https://dl.iosvizor.net/esign/esign_v5.0.2.ipa", "app")
db.add_game(
    "incredibox",
    "https://dl.iosvizor.net/incredibox/Incredibox-v1.3.0-iosvizor.ipa",
    "game")
db.add_game(
    "life is strange",
    "https://dl.iosvizor.net/life-is-strange/30959-Life-Is-Strange-v1-1-11.ipa",
    "game")
db.add_game(
    "the sun origin",
    "https://dl.iosvizor.net/the-sun-origin/30790-the-sun-origin-v1.211.ipa",
    "game")
db.add_game(
    "zona project",
    "https://dl.iosvizor.net/zona-project-x/30268-z.o.n.a-project-x-v1.022.ipa",
    "game")
db.add_game(
    "ghost hunter idle",
    "https://dl.iosvizor.net/ghost-hunter-idle/ghost-hunter-idle-v21-2-0.ipa",
    "game")
db.add_game("war dragons",
            "https://dl.iosvizor.net/war-dragons/war-dragons-v9-40.ipa",
            "game")
db.add_game("rally horizon",
            "https://dl.iosvizor.net/rally-horizon/rally-horizon-v2-5-1.ipa",
            "game")
db.add_game("https://dl.iosvizor.net/threads/threads-v377-0-0.ipa", "app")
db.add_game("pandoland",
            "https://dl.iosvizor.net/pandoland/pandoland-v3-3-1.ipa", "game")
db.add_game("ala mobile gp",
            "https://dl.iosvizor.net/ala-mobile-gp/ala-mobile-gp-v7-5-3.ipa",
            "game")
db.add_game("apex racing",
            "https://dl.iosvizor.net/apex-racing/apex-racing-v1-35-10.ipa",
            "game")
db.add_game("real racing 3",
            "https://dl.iosvizor.net/real-racing-3/real-racing-3-13-0-6.ipa",
            "game")
db.add_game(
    "roblox delta",
    "https://dl.iosvizor.net/roblox-delta/roblox-delta-v2-668-658.ipa", "game")
db.add_game(
    "stick war legacy",
    "https://dl.iosvizor.net/stick-war-legacy/stick-war-legacy-v2023-5-907.ipa",
    "game")
db.add_game(
    "horizon chase 2",
    "https://dl.iosvizor.net/horizon-chase-2/horizon-chase-2-v1.6.6.ipa",
    "game")
db.add_game(
    "asphalt legends unite",
    "https://dl.iosvizor.net/asphalt-legends-unite/asphalt-legends-unite-v24-4-0.ipa",
    "game")
db.add_game(
    "grid legends",
    "https://dl.iosvizor.net/GRID-Legends-Deluxe-Edition/GRID-Legends-Deluxe-Edition-v1.1.3-iosvizor.ipa",
    "game")
db.add_game("rally horizon",
            "https://dl.iosvizor.net/rally-horizon/rally-horizon-v2-5-1.ipa",
            "game")
db.add_game("f1 2016", "https://dl.iosvizor.net/f1-2016/F1-2016-v1-0.ipa",
            "game")
db.add_game(
    "epic conquest 2",
    "https://dl.iosvizor.net/epic-conquest-2/epic-conquest-2-v3-0-2.ipa",
    "game")
db.add_game("prisma", "https://dl.iosvizor.net/prisma/prisma-v4-8-0.ipa",
            "app")
db.add_game("dslr camera",
            "https://dl.iosvizor.net/dslr-camera/dslr-camera-v10-9.ipa", "app")
db.add_game("izip", "https://dl.iosvizor.net/izip-pro/izip-pro-v20.61.ipa",
            "app")
db.add_game("peachy", "https://dl.iosvizor.net/peachy/peachy-v2-2-1.ipa",
            "app")
db.add_game("snapseed", "https://dl.iosvizor.net/snapseed/Snapseed_2.0.4.ipa",
            "app")
db.add_game("tiktok bh",
            "https://dl.iosvizor.net/tiktok/tiktok-bh-plus-38-2-0.ipa", "app")
db.add_game("instagram",
            "https://dl.iosvizor.net/instagram/instagram-v379.0.0.ipa", "app")
db.add_game(
    "nba 2k25 arcade",
    "https://dl.iosvizor.net/nba-2k25-arcade-edition/nba-2k25-arcade-edition-v1.20.ipa",
    "game")
db.add_game(
    "hero blitz",
    "https://dl.iosvizor.net/hero-blitz-rpg-roguelike/hero-blitz-rpg-roguelike-v1-6-1.ipa",
    "game")
db.add_game(
    "marvel contest of champions",
    "https://dl.iosvizor.net/marvel-contest-of-champions/marvel-contest-of-champions-v51-0-0.ipa",
    "game")
db.add_game("zooba", "https://dl.iosvizor.net/zooba/zooba-v5-15-1.ipa", "game")
db.add_game(
    "infinite reflect",
    "https://dl.iosvizor.net/infinite-reflect-photo-editor/infinite-reflect-photo-editor-v1-1.ipa",
    "app")
db.add_game(
    "adobe premier rush",
    "https://dl.iosvizor.net/adobe-premiere-rush-for-video/adobe-premiere-rush-for-video-v2-10.ipa",
    "app")
db.add_game(
    "snow ai profile",
    "https://dl.iosvizor.net/snow-ai-profile/snow-ai-profile-v14-1-10.ipa")
db.add_game("airbrush", "https://dl.iosvizor.net/airbrush/airbrush-v7-7-0.ipa",
            "app")

print("✅ Database created and sample games added!")
