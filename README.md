# Gym Tracker Data

This repository stores workout data for the Gym Tracker Discord bot.

## Structure

- `routines.json` - Saved gym routines
- `prs.json` - Personal records
- `workouts/` - Individual workout logs
- `active/` - Currently active workouts

## View Your Workouts

Visit: `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/` (once GitHub Pages is enabled)

## Bot Commands

```
/routine_add name:Push exercises:Bench Press,Incline Dumbbell,Tricep Pushdown
/routine_list
/start routine_name:Push
/log exercise:Bench Press weight:100 reps:5
/prs
/history
/end
```

## Deployment

This bot is hosted on Railway. To deploy:
1. Fork/clone this repo
2. Create a new project on Railway
3. Link to this GitHub repo
4. Set environment variables:
   - `DISCORD_TOKEN` - Your Discord bot token
   - `GITHUB_TOKEN` - GitHub personal access token
   - `GITHUB_REPO` - username/repo-name
