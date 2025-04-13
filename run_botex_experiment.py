# This script runs a botex experiment using the oTree server.

from dotenv import load_dotenv
from os import environ, makedirs, path
import json
import random
import logging
import botex
import os
import datetime
import sys
import shutil
import subprocess
import sqlite3
import glob

# Set up base output directory
base_output_dir = "botex_data"
makedirs(base_output_dir, exist_ok=True)

# Set up logging to console initially
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables from .env file
if os.path.exists('.env'):
    load_dotenv()
    os.environ['OTREE_REST_KEY'] = environ.get('OTREE_REST_KEY', '')
    logger.info("Loaded environment variables from .env file")

# Reset oTree database
logger.info("Resetting oTree database...")
try:
    subprocess.run(["otree", "resetdb", "--noinput"], check=True)
    logger.info("oTree database reset successful")
except subprocess.CalledProcessError as e:
    logger.error(f"Failed to reset oTree database: {e}")
    print(f"Failed to reset oTree database: {e}")
    sys.exit(1)

# LLM model vars - using Gemini as in your original script
LLM_MODEL = "gemini/gemini-1.5-flash"
LLM_API_KEY = environ.get('OTREE_GEMINI_API_KEY')

# Verify API key exists
if not LLM_API_KEY:
    logger.error("OTREE_GEMINI_API_KEY not found in environment variables")
    print("\nError: OTREE_GEMINI_API_KEY not found in environment variables")
    print("Make sure to set this in your .env file")
    sys.exit(1)

# Start the oTree server
otree_process = None
try:
    # Start oTree server
    logger.info("Starting oTree server...")
    otree_process = botex.start_otree_server(project_path=".")
    
    # Get the available session configurations
    logger.info("Getting session configurations...")
    session_configs = botex.get_session_configs(
        otree_server_url="http://localhost:8000"
    )
    
    # Set up temporary database for session initialization
    temp_db = os.path.join(base_output_dir, "temp_botex.sqlite3")
    if os.path.exists(temp_db):
        os.remove(temp_db)
    
    # Initialize a session with the temporary database
    logger.info("Initializing oTree session...")
    session = botex.init_otree_session(
        config_name='group_number_guess',
        npart=3,
        otree_server_url="http://localhost:8000",
        botex_db=temp_db
    )
    
    session_id = session['session_id']
    logger.info(f"Session initialized with ID: {session_id}")
    
    # Create session-specific output directory
    output_dir = os.path.join(base_output_dir, f"session_{session_id}")
    makedirs(output_dir, exist_ok=True)
    
    # Set up the log file in the session-specific directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = path.join(output_dir, f"experiment_log_{timestamp}.txt")
    
    # Add file handler to logger
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    logger.info(f"Session output directory: {output_dir}")
    logger.info(f"Log file: {log_file}")
    
    # Create final database in the session directory
    botex_db = path.join(output_dir, f"botex_{session_id}.sqlite3")
    
    # Copy the temporary database to the session directory
    if os.path.exists(temp_db):
        shutil.copy2(temp_db, botex_db)
        logger.info(f"Copied database to: {botex_db}")
    
    # Define output filenames
    botex_responses_csv = path.join(output_dir, f"botex_{session_id}_responses.csv")
    otree_wide_csv = path.join(output_dir, f"otree_{session_id}_wide.csv")
    
    # Run the bots on the session
    monitor_url = f"http://localhost:8000/SessionMonitor/{session_id}"
    logger.info(f"Starting bots. You can monitor their progress at {monitor_url}")
    print(f"\nStarting bots. You can monitor their progress at {monitor_url}")
    
    # Run bots on the session with throttling only - no custom retry parameters
    botex.run_bots_on_session(
        session_id=session_id,
        botex_db=botex_db,
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        throttle=True  # Use throttling to avoid rate limits
    )
    
    # Export oTree data
    logger.info("Exporting oTree data...")
    botex.export_otree_data(
        otree_wide_csv,
        server_url="http://localhost:8000",
        admin_name='admin',
        admin_password=environ.get('OTREE_ADMIN_PASSWORD', 'admin')
    )
    
    # Normalize and export to CSV
    logger.info("Normalizing oTree data...")
    normalized_data = botex.normalize_otree_data(
        otree_wide_csv, 
        store_as_csv=True,
        data_exp_path=output_dir,
        exp_prefix=f"otree_{session_id}"
    )
    
    # Try to export botex responses
    try:
        logger.info("Exporting botex response data...")
        botex.export_response_data(
            botex_responses_csv,
            botex_db=botex_db,
            session_id=session_id
        )
        logger.info("Bot responses successfully exported")
    except Exception as e:
        logger.warning(f"No bot responses could be exported: {str(e)}")
        logger.info("This may happen if bots didn't complete any form submissions")
        
        # Creating an empty response file with header
        with open(botex_responses_csv, 'w') as f:
            f.write("session_id,participant_id,round,question_id,answer,reason\n")
            f.write(f"# No responses recorded for session {session_id}\n")
    
    # Keep only the specific CSV files you want
    logger.info("Cleaning up CSV files...")
    
    # Keep only game_player file from normalized data
    for csv_file in glob.glob(os.path.join(output_dir, f"otree_{session_id}*.csv")):
        filename = os.path.basename(csv_file)
        if not ("game_player" in filename or f"botex_{session_id}_responses" in filename):
            os.remove(csv_file)
            logger.info(f"Removed {filename}")
    
    # Create a summary file
    summary_file = path.join(output_dir, f"experiment_summary_{session_id}.txt")
    with open(summary_file, 'w') as f:
        f.write(f"Experiment Summary - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*50 + "\n\n")
        f.write(f"Session ID: {session_id}\n")
        f.write(f"Model used: {LLM_MODEL}\n")
        f.write(f"Number of participants: 3\n\n")
        f.write("Files generated:\n")
        f.write(f"- Log file: {path.basename(log_file)}\n")
        f.write(f"- Bot responses: {path.basename(botex_responses_csv)}\n")
        
        # Include the game player file
        game_player_files = [f for f in os.listdir(output_dir) if "game_player" in f]
        if game_player_files:
            f.write("Game player data:\n")
            for file in game_player_files:
                f.write(f"- {file}\n")
        
        # Add troubleshooting information
        f.write("\nTroubleshooting Notes:\n")
        f.write("- Make sure Game.html has a visible otree-btn-next element\n")
        f.write("- Bots need to be able to find and click form submit buttons\n")
    
    logger.info(f"Experiment complete. All outputs saved to {output_dir} folder")

except Exception as e:
    logger.error(f"Error running experiment: {str(e)}", exc_info=True)
    print(f"\nError running experiment: {str(e)}")

finally:
    # Clean up temporary database
    if os.path.exists(temp_db):
        try:
            os.remove(temp_db)
        except:
            pass
    
    # Stop the oTree server
    if otree_process:
        try:
            logger.info("Stopping oTree server...")
            botex.stop_otree_server(otree_process)
        except Exception as e:
            logger.error(f"Error stopping oTree server: {str(e)}")