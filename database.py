import sqlite3
import config

class Database:
    def __init__(self):
        self.init_databases()

    def init_databases(self):
        """Инициализирует базы данных и таблицы"""
        try:
            # Таблица приложений
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS apps (
                name TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                content_type TEXT DEFAULT 'game',
                category TEXT DEFAULT 'other',
                version TEXT DEFAULT 'N/A',
                updated TEXT DEFAULT 'N/A',
                genre TEXT DEFAULT 'N/A',
                developer TEXT DEFAULT 'N/A',
                size TEXT DEFAULT 'N/A',
                date_added TEXT DEFAULT CURRENT_TIMESTAMP
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_name TEXT NOT NULL,
                rating INTEGER NOT NULL,
                rated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, game_name)
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS rating_boosts (
                game_name TEXT PRIMARY KEY,
                virtual_count INTEGER NOT NULL,
                virtual_avg REAL NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_name TEXT NOT NULL,
                version TEXT DEFAULT 'N/A',
                problem_type TEXT NOT NULL,
                comment TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, game_name, version)
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''')

            # Таблица предложений
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                date_added TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            conn.commit()
            conn.close()

            # Таблица пользователей
            conn = sqlite3.connect(config.DB_NAME_USERS)
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                downloads_left INTEGER DEFAULT 5,
                is_premium INTEGER DEFAULT 0,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            conn.commit()
            conn.close()

            # Таблица загрузок (добавлена)
            conn = sqlite3.connect(config.DB_NAME_USERS)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    game_name TEXT NOT NULL,
                    download_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (game_name) REFERENCES apps(name)
                )
            """)
            conn.commit()
            conn.close()

            return True
        except Exception as e:
            print(f"Database initialization error: {e}")
            return False

    def _ensure_ratings_table(self, cursor):
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_name TEXT NOT NULL,
            rating INTEGER NOT NULL,
            rated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, game_name)
        )''')

    def _ensure_rating_boosts_table(self, cursor):
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rating_boosts (
            game_name TEXT PRIMARY KEY,
            virtual_count INTEGER NOT NULL,
            virtual_avg REAL NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
    def _ensure_reports_table(self, cursor):
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_name TEXT NOT NULL,
            version TEXT DEFAULT 'N/A',
            problem_type TEXT NOT NULL,
            comment TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, game_name, version)
        )''')

    def _ensure_screenshots_table(self, cursor):
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS screenshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            file_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')


    def update_game(self, old_name, new_name, new_url):
        """Обновляет данные игры в базе"""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()

            cursor.execute("SELECT 1 FROM apps WHERE name = ?", (old_name.lower(),))
            if not cursor.fetchone():
                conn.close()
                return False

            if old_name.lower() == new_name.lower():
                cursor.execute("UPDATE apps SET url = ? WHERE name = ?",
                             (new_url, old_name.lower()))
            else:
                cursor.execute("DELETE FROM apps WHERE name = ?", (old_name.lower(),))
                cursor.execute("INSERT INTO apps (name, url) VALUES (?, ?)",
                             (new_name.lower(), new_url))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Game update error: {e}")
            return False

    def add_game(self, name, url, content_type='game', category='other', version='N/A', updated='N/A', genre='N/A', developer='N/A', size='N/A'):
        """Добавляет новую игру или приложение в базу"""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()

            # Check if columns exist, add if not
            cursor.execute("PRAGMA table_info(apps)")
            columns = [col[1] for col in cursor.fetchall()]
            
            new_cols = {
                'category': "TEXT DEFAULT 'other'",
                'version': "TEXT DEFAULT 'N/A'",
                'updated': "TEXT DEFAULT 'N/A'",
                'genre': "TEXT DEFAULT 'N/A'",
                'developer': "TEXT DEFAULT 'N/A'",
                'size': "TEXT DEFAULT 'N/A'"
            }
            
            for col_name, col_def in new_cols.items():
                if col_name not in columns:
                    cursor.execute(f"ALTER TABLE apps ADD COLUMN {col_name} {col_def}")
            conn.commit()

            # Check if game exists
            cursor.execute("SELECT 1 FROM apps WHERE name = ?", (name.lower(),))
            if cursor.fetchone():
                # Update if exists
                cursor.execute("""
                    UPDATE apps SET 
                        url = ?, content_type = ?, category = ?, 
                        version = ?, updated = ?, genre = ?, developer = ?, size = ? 
                    WHERE name = ?""",
                             (url, content_type, category, version, updated, genre, developer, size, name.lower()))
            else:
                # Insert new if doesn't exist
                cursor.execute("""
                    INSERT INTO apps (name, url, content_type, category, version, updated, genre, developer, size) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                             (name.lower(), url, content_type, category, version, updated, genre, developer, size))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Add game error: {e}")
            return False

    def get_all_games(self):
        """Возвращает список всех игр"""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()

            cursor.execute("PRAGMA table_info(apps)")
            columns = [col[1] for col in cursor.fetchall()]
            
            needed_cols = ['content_type', 'category', 'version', 'updated', 'genre', 'developer', 'size']
            for col in needed_cols:
                if col not in columns:
                    cursor.execute(f"ALTER TABLE apps ADD COLUMN {col} TEXT DEFAULT 'N/A'")
            conn.commit()

            cursor.execute("SELECT name, url, content_type, category, version, updated, genre, developer, size FROM apps ORDER BY name")
            games = cursor.fetchall()
            conn.close()
            return games
        except Exception as e:
            print(f"Get games error: {e}")
            return []

    def add_suggestion(self, user_id, name, url):
        """Добавляет предложение в базу"""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO suggestions (user_id, name, url) VALUES (?, ?, ?)",
                         (user_id, name.lower(), url))
            suggestion_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return suggestion_id
        except Exception as e:
            print(f"Add suggestion error: {e}")
            return None

    def get_pending_suggestions(self):
        """Возвращает список ожидающих предложений"""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, name, url FROM suggestions WHERE status = 'pending'")
            suggestions = cursor.fetchall()
            conn.close()
            return suggestions
        except Exception as e:
            print(f"Get suggestions error: {e}")
            return []

    def get_suggestion_by_id(self, suggestion_id):
        """Р’РѕР·РІСЂР°С‰Р°РµС‚ РїСЂРµРґР»РѕР¶РµРЅРёРµ РїРѕ ID"""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, name, url, status FROM suggestions WHERE id = ?", (suggestion_id,))
            suggestion = cursor.fetchone()
            conn.close()
            return suggestion
        except Exception as e:
            print(f"Get suggestion error: {e}")
            return None

    def update_suggestion_status(self, suggestion_id, status):
        """РћР±РЅРѕРІР»СЏРµС‚ СЃС‚Р°С‚СѓСЃ РїСЂРµРґР»РѕР¶РµРЅРёСЏ"""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            cursor.execute("UPDATE suggestions SET status = ? WHERE id = ?", (status, suggestion_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Update suggestion status error: {e}")
            return False

    def get_user(self, user_id):
        """Получает данные пользователя"""
        try:
            conn = sqlite3.connect(config.DB_NAME_USERS)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()
            return user
        except Exception as e:
            print(f"Get user error: {e}")
            return None

    def create_user(self, user_id):
        """Создает нового пользователя"""
        try:
            conn = sqlite3.connect(config.DB_NAME_USERS)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Create user error: {e}")
            return False

    def update_user_activity(self, user_id):
        """Обновляет время последней активности"""
        try:
            conn = sqlite3.connect(config.DB_NAME_USERS)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Update activity error: {e}")
            return False

    def approve_suggestion(self, suggestion_id):
        """Одобряет предложение и добавляет его в базу игр"""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()

            # Get suggestion details
            cursor.execute("SELECT name, url FROM suggestions WHERE id = ?", (suggestion_id,))
            suggestion = cursor.fetchone()
            if not suggestion:
                return False

            name, url = suggestion

            # Add to apps table
            cursor.execute("INSERT INTO apps (name, url) VALUES (?, ?)", (name, url))

            # Update suggestion status
            cursor.execute("UPDATE suggestions SET status = 'approved' WHERE id = ?", (suggestion_id,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Approve suggestion error: {e}")
            return False

    def add_download(self, user_id, game_name):
        """Adds a new download record to the database."""
        try:
            conn = sqlite3.connect(config.DB_NAME_USERS)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO downloads (user_id, game_name) VALUES (?, ?)", (user_id, game_name))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Add download error: {e}")
            return False


    def get_user_downloads(self, user_id):
        """Получает историю загрузок пользователя"""
        try:
            conn = sqlite3.connect(config.DB_NAME_USERS)
            cursor = conn.cursor()
            
            # Attach apps database to perform JOIN across files
            cursor.execute(f"ATTACH DATABASE '{config.DB_NAME_APPS}' AS apps_db")
            
            cursor.execute("""
                SELECT d.game_name, d.download_date, a.url
                FROM downloads d
                JOIN apps_db.apps a ON LOWER(d.game_name) = LOWER(a.name)
                WHERE d.user_id = ? 
                ORDER BY d.download_date DESC
                """, (user_id,))
            downloads = cursor.fetchall()
            conn.close()
            return downloads
        except Exception as e:
            print(f"Get user downloads error: {e}")
            return []

    def get_game_recommendations(self, game_name, limit=3):
        """Получает рекомендации игр на основе категории"""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            
            # Get the category of the downloaded game
            cursor.execute("SELECT category FROM apps WHERE name = ?", (game_name.lower(),))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return []
            
            category = result[0]
            
            # Get other games in the same category
            cursor.execute("""
                SELECT name FROM apps 
                WHERE category = ? AND name != ? 
                ORDER BY RANDOM() 
                LIMIT ?
            """, (category, game_name.lower(), limit))
            
            recommendations = [row[0] for row in cursor.fetchall()]
            conn.close()
            return recommendations
            
        except Exception as e:
            print(f"Get recommendations error: {e}")
            return []

    def get_stats(self):
        """Возвращает статистику бота"""
        try:
            stats = {}
            
            # Пользователи
            conn_users = sqlite3.connect(config.DB_NAME_USERS)
            cursor_users = conn_users.cursor()
            cursor_users.execute("SELECT COUNT(*), SUM(is_premium) FROM users")
            total_users, premium_users = cursor_users.fetchone()
            stats['total_users'] = total_users
            stats['premium_users'] = premium_users or 0
            
            # Загрузки
            cursor_users.execute("SELECT COUNT(*) FROM downloads")
            stats['total_downloads'] = cursor_users.fetchone()[0]
            conn_users.close()
            
            # Игры
            conn_apps = sqlite3.connect(config.DB_NAME_APPS)
            cursor_apps = conn_apps.cursor()
            cursor_apps.execute("SELECT COUNT(*) FROM apps")
            stats['total_apps'] = cursor_apps.fetchone()[0]
            conn_apps.close()
            
            return stats
        except Exception as e:
            print(f"Get stats error: {e}")
            return None

    def add_or_update_rating(self, user_id, game_name, rating):
        """Adds or updates a user's rating for a game."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            self._ensure_ratings_table(cursor)
            cursor.execute("""
                INSERT INTO ratings (user_id, game_name, rating)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, game_name)
                DO UPDATE SET rating = excluded.rating, rated_at = CURRENT_TIMESTAMP
            """, (user_id, game_name.lower(), int(rating)))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Add rating error: {e}")
            return False

    def delete_rating(self, user_id, game_name):
        """Deletes a user's rating for a game; returns count."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            self._ensure_ratings_table(cursor)
            cursor.execute(
                "DELETE FROM ratings WHERE user_id = ? AND game_name = ?",
                (int(user_id), game_name.lower())
            )
            conn.commit()
            count = cursor.rowcount
            conn.close()
            return count
        except Exception as e:
            print(f"Delete rating error: {e}")
            return 0

    def delete_ratings_for_game(self, game_name):
        """Deletes all ratings for a game; returns count."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            self._ensure_ratings_table(cursor)
            cursor.execute(
                "DELETE FROM ratings WHERE game_name = ?",
                (game_name.lower(),)
            )
            conn.commit()
            count = cursor.rowcount
            conn.close()
            return count
        except Exception as e:
            print(f"Delete ratings error: {e}")
            return 0

    def get_game_rating_stats(self, game_name):
        """Returns average rating and count for a game."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            self._ensure_ratings_table(cursor)
            cursor.execute("SELECT AVG(rating), COUNT(*) FROM ratings WHERE game_name = ?", (game_name.lower(),))
            avg_rating, count = cursor.fetchone()
            conn.close()
            return (avg_rating, count)
        except Exception as e:
            print(f"Get rating stats error: {e}")
            return (None, 0)

    def get_virtual_rating(self, game_name):
        """Returns virtual average and count for a game."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            self._ensure_rating_boosts_table(cursor)
            cursor.execute(
                "SELECT virtual_avg, virtual_count FROM rating_boosts WHERE game_name = ?",
                (game_name.lower(),)
            )
            row = cursor.fetchone()
            conn.close()
            return (row[0], row[1]) if row else (0.0, 0)
        except Exception as e:
            print(f"Get virtual rating error: {e}")
            return (0.0, 0)

    def set_virtual_rating(self, game_name, virtual_avg, virtual_count):
        """Sets virtual average and count for a game."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            self._ensure_rating_boosts_table(cursor)
            cursor.execute(
                """
                INSERT INTO rating_boosts (game_name, virtual_avg, virtual_count)
                VALUES (?, ?, ?)
                ON CONFLICT(game_name) DO UPDATE SET
                    virtual_avg = excluded.virtual_avg,
                    virtual_count = excluded.virtual_count,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (game_name.lower(), float(virtual_avg), int(virtual_count))
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Set virtual rating error: {e}")
            return False

    def add_virtual_rating(self, game_name, virtual_avg, virtual_count):
        """Adds virtual rating votes to existing virtual rating."""
        try:
            current_avg, current_count = self.get_virtual_rating(game_name)
            new_count = int(virtual_count)
            if new_count < 0:
                return False
            if current_count <= 0:
                return self.set_virtual_rating(game_name, virtual_avg, new_count)

            total_count = current_count + new_count
            total_sum = (current_avg * current_count) + (float(virtual_avg) * new_count)
            total_avg = total_sum / total_count if total_count > 0 else float(virtual_avg)
            return self.set_virtual_rating(game_name, total_avg, total_count)
        except Exception as e:
            print(f"Add virtual rating error: {e}")
            return False

    def clear_virtual_rating(self, game_name):
        """Clears virtual rating for a game; returns count."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            self._ensure_rating_boosts_table(cursor)
            cursor.execute(
                "DELETE FROM rating_boosts WHERE game_name = ?",
                (game_name.lower(),)
            )
            conn.commit()
            count = cursor.rowcount
            conn.close()
            return count
        except Exception as e:
            print(f"Clear virtual rating error: {e}")
            return 0

    def get_game_id_by_name(self, name):
        """Returns rowid for a game/app by name."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            cursor.execute("SELECT rowid FROM apps WHERE name = ?", (name.lower(),))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            print(f"Get game id error: {e}")
            return None

    def game_exists_by_id(self, item_id):
        """Checks if a game/app exists by rowid."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM apps WHERE rowid = ?", (item_id,))
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except Exception as e:
            print(f"Check game id error: {e}")
            return False

    def get_game_by_name(self, name):
        """Returns a single game/app record by name."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, url, content_type, category, version, updated, genre, developer, size FROM apps WHERE name = ?",
                (name.lower(),)
            )
            game = cursor.fetchone()
            conn.close()
            return game
        except Exception as e:
            print(f"Get game error: {e}")
            return None

    def add_report(self, user_id, game_name, version, problem_type, comment=""):
        """Adds a report; returns False if duplicate or on error."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            self._ensure_reports_table(cursor)
            version_value = version or "N/A"

            cursor.execute(
                "SELECT 1 FROM reports WHERE user_id = ? AND game_name = ? AND version = ?",
                (user_id, game_name.lower(), version_value)
            )
            if cursor.fetchone():
                conn.close()
                return False

            cursor.execute("""
                INSERT INTO reports (user_id, game_name, version, problem_type, comment)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, game_name.lower(), version_value, problem_type, comment or ""))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Add report error: {e}")
            return False

    def add_screenshot(self, item_id, file_id):
        """Adds a screenshot for an item."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            self._ensure_screenshots_table(cursor)
            cursor.execute(
                "INSERT INTO screenshots (item_id, file_id) VALUES (?, ?)",
                (int(item_id), file_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Add screenshot error: {e}")
            return False

    def get_screenshots(self, item_id, limit=10):
        """Returns screenshot file_ids for an item."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            self._ensure_screenshots_table(cursor)
            cursor.execute(
                "SELECT file_id FROM screenshots WHERE item_id = ? ORDER BY id LIMIT ?",
                (int(item_id), int(limit))
            )
            rows = cursor.fetchall()
            conn.close()
            return [row[0] for row in rows]
        except Exception as e:
            print(f"Get screenshots error: {e}")
            return []

    def delete_screenshots_by_item(self, item_id):
        """Deletes all screenshots for an item; returns count."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            self._ensure_screenshots_table(cursor)
            cursor.execute("DELETE FROM screenshots WHERE item_id = ?", (int(item_id),))
            conn.commit()
            count = cursor.rowcount
            conn.close()
            return count
        except Exception as e:
            print(f"Delete screenshots error: {e}")
            return 0

    def delete_screenshot_by_id(self, photo_id):
        """Deletes a single screenshot by id; returns count."""
        try:
            conn = sqlite3.connect(config.DB_NAME_APPS)
            cursor = conn.cursor()
            self._ensure_screenshots_table(cursor)
            cursor.execute("DELETE FROM screenshots WHERE id = ?", (int(photo_id),))
            conn.commit()
            count = cursor.rowcount
            conn.close()
            return count
        except Exception as e:
            print(f"Delete screenshot error: {e}")
            return 0

# Create global database instance
db = Database()

if __name__ == "__main__":
    print("✅ Базы данных успешно инициализированы")
    # Добавляем тестовые данные
    db.update_game("test", "terraria", "https://example.com/terraria.ipa")
    db.update_game("test2", "minecraft", "https://example.com/minecraft.ipa")
    print("Список игр в базе:")
    for name, url in db.get_all_games():
        print(f"- {name}: {url}")
    db.add_download(123, "terraria") #Example add download
    print(db.get_user_downloads(123))

