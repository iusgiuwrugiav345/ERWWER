
from database import db

# Define game categories
GAME_CATEGORIES = {
    # Racing games
    'real racing 3': 'racing',
    'apex racing': 'racing',
    'horizon chase 2': 'racing',
    'asphalt legends unite': 'racing',
    'grid legends': 'racing',
    'rally horizon': 'racing',
    'f1 2016': 'racing',
    'nfs most wanted': 'racing',
    'rush rally origins': 'racing',
    'rush rally 3': 'racing',
    'driving zone 2': 'racing',
    
    # Adventure/Action games
    'minecraft': 'adventure',
    'gta vice city': 'action',
    'gta san andreas': 'action',
    'stardew valley': 'adventure',
    'getting over it': 'adventure',
    'human fall flat': 'adventure',
    'plague inc': 'strategy',
    'resident evil village': 'horror',
    'resident evil 4': 'horror',
    'goat simulator': 'simulation',
    'pou': 'simulation',
    'geometry dash': 'arcade',
    'bully': 'action',
    'mortal combat x': 'fighting',
    'limbo': 'puzzle',
    'machinarium': 'puzzle',
    'true skate': 'sports',
    'forager': 'adventure',
    'day r': 'survival',
    'motorsport manager 4': 'simulation',
    'wrc': 'racing',
    'bridge constructor': 'puzzle',
    'monopoly': 'board',
    'hitman sniper': 'action',
    'atom rpg': 'rpg',
    'guitar hero live': 'music',
    'max payne': 'action',
    'earn to die 2': 'action',
    'balatro': 'card',
    'roblox delta': 'sandbox',
    'stick war legacy': 'strategy',
    'epic conquest 2': 'rpg',
    'nba 2k25 arcade': 'sports',
    'hero blitz': 'rpg',
    'marvel contest of champions': 'fighting',
    'zooba': 'battle',
    'incredibox': 'music',
    'life is strange': 'adventure',
    'the sun origin': 'survival',
    'zona project': 'survival',
    'ghost hunter idle': 'idle',
    'war dragons': 'strategy',
    'pandoland': 'adventure',
    'ala mobile gp': 'racing',
    'real flight simulator': 'simulation',
    
    # Apps
    'fl studio mobile': 'music',
    'youtube plus': 'media',
    'whatsapp messenger': 'social',
    'prisma': 'photo',
    'dslr camera': 'photo',
    'izip': 'utility',
    'peachy': 'photo',
    'snapseed': 'photo',
    'tiktok bh': 'social',
    'instagram': 'social',
    'infinite reflect': 'photo',
    'adobe premier rush': 'video',
    'snow ai profile': 'photo',
    'airbrush': 'photo',
    'video star': 'video',
    'esign': 'utility'
}

def update_game_categories():
    """Updates existing games with their categories"""
    print("Updating game categories...")
    
    for game_name, category in GAME_CATEGORIES.items():
        game = db.get_game_by_name(game_name)
        if game:
            name, url, content_type, _ = game
            db.add_game(name, url, content_type, category)
            print(f"Updated {game_name} -> {category}")
        else:
            print(f"Game not found: {game_name}")
    
    print("Category update complete!")

if __name__ == "__main__":
    update_game_categories()
