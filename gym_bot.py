#!/usr/bin/env python3
"""
Gym Tracker Discord Bot
- Hosted on Railway (or any cloud platform)
- Stores data in GitHub repo via API
- No local database needed
"""

import os
import json
import discord
from discord import app_commands
from datetime import datetime
import aiohttp
import asyncio

# ===== CONFIGURATION (Set these via environment variables) =====
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', '')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_REPO = os.getenv('GITHUB_REPO', '')  # format: username/repo-name
GUILD_ID = None  # Set to None to allow all servers, or set guild ID

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# In-memory cache for routines (fetched from GitHub)
routines_cache = {}
cache_loaded = False

async def github_request(method, path, data=None):
    """Make a GitHub API request"""
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    url = f'https://api.github.com/repos/{GITHUB_REPO}/{path}'
    
    async with aiohttp.ClientSession() as session:
        if method == 'GET':
            async with session.get(url, headers=headers) as resp:
                if resp.status == 404:
                    return None
                return await resp.json()
        elif method == 'PUT':
            async with session.put(url, headers=headers, json=data) as resp:
                return await resp.json()

async def get_file(path):
    """Get file content from GitHub"""
    result = await github_request('GET', f'contents/{path}')
    if result and 'content' in result:
        import base64
        return json.loads(base64.b64decode(result['content']).decode('utf-8')), result['sha']
    return None, None

async def save_file(path, content, message, sha=None):
    """Save file to GitHub"""
    import base64
    data = {
        'message': message,
        'content': base64.b64encode(json.dumps(content, indent=2).encode('utf-8')).decode('utf-8')
    }
    if sha:
        data['sha'] = sha
    return await github_request('PUT', f'contents/{path}', data)

async def load_routines():
    """Load routines from GitHub"""
    global routines_cache, cache_loaded
    data, _ = await get_file('routines.json')
    if data:
        routines_cache = data
    else:
        routines_cache = {}
    cache_loaded = True

async def save_routines():
    """Save routines to GitHub"""
    await save_file('routines.json', routines_cache, 'Update routines')

@client.event
async def on_ready():
    await load_routines()
    # Sync commands globally (or to specific guild)
    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)
    else:
        await tree.sync()
    print(f'Gym Bot is online: {client.user}')

# ===== COMMANDS =====

@tree.command(name="routine_add", description="Create a new gym routine")
async def routine_add(interaction: discord.Interaction, name: str, exercises: str):
    if not cache_loaded:
        await load_routines()
    
    exercises_list = [e.strip() for e in exercises.split(',')]
    routines_cache[name.lower()] = {
        'name': name,
        'exercises': exercises_list,
        'created_by': str(interaction.user),
        'created_at': datetime.now().isoformat()
    }
    await save_routines()
    await interaction.response.send_message(f"✅ Routine **{name}** created with {len(exercises_list)} exercises: {', '.join(exercises_list)}")

@tree.command(name="routine_list", description="List all gym routines")
async def routine_list(interaction: discord.Interaction):
    if not cache_loaded:
        await load_routines()
    
    if not routines_cache:
        await interaction.response.send_message("No routines created yet! Use `/routine_add` to create one.")
        return
    
    msg = "**Your Routines:**\n"
    for name, data in routines_cache.items():
        msg += f"- **{data['name']}**: {', '.join(data['exercises'])}\n"
    await interaction.response.send_message(msg)

@tree.command(name="start", description="Start a workout for a routine")
async def start_workout(interaction: discord.Interaction, routine_name: str):
    if not cache_loaded:
        await load_routines()
    
    routine = routines_cache.get(routine_name.lower())
    if not routine:
        await interaction.response.send_message(f"❌ Routine **{routine_name}** not found! Use `/routine_list` to see available routines.")
        return
    
    # Store active workout in a simple JSON file
    active_workout = {
        'user': str(interaction.user),
        'user_id': interaction.user.id,
        'routine': routine_name,
        'exercises': routine['exercises'],
        'start_time': datetime.now().isoformat(),
        'sets': []
    }
    
    # Save to GitHub
    filename = f"active/{interaction.user.id}.json"
    await save_file(filename, active_workout, f'Start workout for {interaction.user}')
    
    msg = f"🏋️ Starting **{routine_name}** workout!\n\n**Exercises:**\n"
    msg += "\n".join([f"- {ex}" for ex in routine['exercises']])
    msg += "\n\nLog sets with: `/log <exercise> <weight> <reps>`"
    await interaction.response.send_message(msg)

@tree.command(name="log", description="Log a set for an exercise")
async def log_set(interaction: discord.Interaction, exercise: str, weight: float, reps: int):
    filename = f"active/{interaction.user.id}.json"
    workout, sha = await get_file(filename)
    
    if not workout:
        await interaction.response.send_message("❌ No active workout! Use `/start <routine>` first.")
        return
    
    # Add set
    workout['sets'].append({
        'exercise': exercise,
        'weight': weight,
        'reps': reps,
        'logged_at': datetime.now().isoformat()
    })
    
    await save_file(filename, workout, f'Log set for {interaction.user}', sha)
    
    # Check if this is a PR (we'll check against saved PRs)
    pr_data, pr_sha = await get_file('prs.json')
    if not pr_data:
        pr_data = {}
    
    exercise_key = exercise.lower()
    is_pr = False
    if exercise_key not in pr_data or weight > pr_data[exercise_key]['weight']:
        pr_data[exercise_key] = {
            'weight': weight,
            'reps': reps,
            'date': datetime.now().isoformat(),
            'user': str(interaction.user)
        }
        await save_file('prs.json', pr_data, f'Update PRs', pr_sha)
        is_pr = True
    
    msg = f"✅ Logged: **{exercise}** {weight}kg x {reps} reps"
    if is_pr:
        msg += " 🎉 **NEW PR!**"
    await interaction.response.send_message(msg)

@tree.command(name="end", description="End current workout and save to history")
async def end_workout(interaction: discord.Interaction):
    filename = f"active/{interaction.user.id}.json"
    workout, sha = await get_file(filename)
    
    if not workout:
        await interaction.response.send_message("❌ No active workout to end!")
        return
    
    # Move to history
    history_file = f"workouts/{datetime.now().strftime('%Y-%m-%d')}_{interaction.user.id}.json"
    workout['end_time'] = datetime.now().isoformat()
    await save_file(history_file, workout, f'Workout completed by {interaction.user}')
    
    # Delete active workout
    # (GitHub delete requires sha)
    await save_file(filename, {'deleted': True}, f'End workout for {interaction.user}', sha)
    
    sets_count = len(workout['sets'])
    await interaction.response.send_message(f"✅ Workout ended! Logged {sets_count} sets. Saved to history.")

@tree.command(name="prs", description="Show all personal records")
async def show_prs(interaction: discord.Interaction):
    pr_data, _ = await get_file('prs.json')
    
    if not pr_data:
        await interaction.response.send_message("No PRs logged yet! Start working out to set some.")
        return
    
    msg = "**Your Personal Records:**\n"
    for exercise, data in pr_data.items():
        msg += f"- **{exercise.title()}**: {data['weight']}kg x {data['reps']} reps (by {data['user']})\n"
    await interaction.response.send_message(msg)

@tree.command(name="history", description="Show your recent workouts")
async def show_history(interaction: discord.Interaction):
    # List workout files for this user
    result = await github_request('GET', f'contents/workouts')
    if not result or not isinstance(result, list):
        await interaction.response.send_message("No workout history found!")
        return
    
    user_workouts = [f for f in result if str(interaction.user.id) in f['name']]
    if not user_workouts:
        await interaction.response.send_message("No workouts logged yet!")
        return
    
    msg = f"**Your Last {min(5, len(user_workouts))} Workouts:**\n"
    for wf in user_workouts[:5]:
        msg += f"- {wf['name'].replace('.json', '').replace('_', ' ')}\n"
    await interaction.response.send_message(msg)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("ERROR: Set DISCORD_TOKEN environment variable")
    elif not GITHUB_TOKEN:
        print("ERROR: Set GITHUB_TOKEN environment variable")
    elif not GITHUB_REPO:
        print("ERROR: Set GITHUB_REPO environment variable (format: username/repo-name)")
    else:
        client.run(DISCORD_TOKEN)
