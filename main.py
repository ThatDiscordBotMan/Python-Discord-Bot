import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up intents (permissions for the bot)
intents = discord.Intents.default()
intents.message_content = True  # Allow bot to read message content

# Set up bot with command prefix
bot = commands.Bot(command_prefix='!', intents=intents)


# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} servers')

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')

        # List all synced commands
        for command in synced:
            print(f'- {command.name}')

    except Exception as e:
        print(f'Failed to sync commands: {e}')


# Event: Someone sends a message
@bot.event
async def on_message(message):
    # Debug: Print all messages (remove this later)
    print(f"Message received: '{message.content}' from {message.author}")

    # Don't respond to the bot's own messages
    if message.author == bot.user:
        return

    # Respond to "hello"
    if message.content.lower() == 'hello':
        await message.channel.send(f'Hello {message.author.mention}!')

    # This line is important - it allows commands to work
    await bot.process_commands(message)


# Simple command (prefix version) - now with latency
@bot.command(name='ping')
async def ping(ctx):
    """Check bot latency and response time"""
    import time

    # Record when we start processing
    start_time = time.time()

    # Send initial message
    message = await ctx.send("Pinging...")

    # Calculate response time
    end_time = time.time()
    response_time = (end_time - start_time) * 1000  # Convert to milliseconds

    # Get websocket latency
    websocket_latency = bot.latency * 1000  # Convert to milliseconds

    # Edit the message with latency info
    embed = discord.Embed(title="🏓 Pong!", color=0x00ff00)
    embed.add_field(name="Response Time", value=f"{response_time:.2f}ms", inline=True)
    embed.add_field(name="WebSocket Latency", value=f"{websocket_latency:.2f}ms", inline=True)

    # Add status indicator based on latency
    if websocket_latency < 100:
        embed.add_field(name="Status", value="🟢 Excellent", inline=True)
    elif websocket_latency < 200:
        embed.add_field(name="Status", value="🟡 Good", inline=True)
    elif websocket_latency < 300:
        embed.add_field(name="Status", value="🟠 Fair", inline=True)
    else:
        embed.add_field(name="Status", value="🔴 Poor", inline=True)

    await message.edit(content="", embed=embed)


# Slash version of ping command
@bot.tree.command(name='ping', description='Check bot latency and response time')
async def ping_slash(interaction: discord.Interaction):
    import time

    # Record start time
    start_time = time.time()

    # Defer the response (since we need time to calculate)
    await interaction.response.defer()

    # Calculate response time
    end_time = time.time()
    response_time = (end_time - start_time) * 1000

    # Get websocket latency
    websocket_latency = bot.latency * 1000

    # Create embed with latency info
    embed = discord.Embed(title="🏓 Pong!", color=0x00ff00)
    embed.add_field(name="Response Time", value=f"{response_time:.2f}ms", inline=True)
    embed.add_field(name="WebSocket Latency", value=f"{websocket_latency:.2f}ms", inline=True)

    # Add status indicator
    if websocket_latency < 100:
        embed.add_field(name="Status", value="🟢 Excellent", inline=True)
    elif websocket_latency < 200:
        embed.add_field(name="Status", value="🟡 Good", inline=True)
    elif websocket_latency < 300:
        embed.add_field(name="Status", value="🟠 Fair", inline=True)
    else:
        embed.add_field(name="Status", value="🔴 Poor", inline=True)

    await interaction.followup.send(embed=embed)


# Command with arguments (prefix version)
@bot.command(name='say')
async def say(ctx, *, message):
    """Make the bot repeat something"""
    await ctx.send(message)


# Slash version of say command
@bot.tree.command(name='say', description='Make the bot repeat something')
async def say_slash(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)


# Slash version of clear command
@bot.tree.command(name='clear', description='Delete a specified number of messages')
async def clear_slash(interaction: discord.Interaction, amount: int):
    # Check if user has manage messages permission
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ You don't have permission to delete messages!", ephemeral=True)
        return

    # Check if bot has manage messages permission
    if not interaction.guild.me.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ I don't have permission to delete messages!", ephemeral=True)
        return

    # Validate amount (Discord limits bulk delete to 100 messages)
    if amount < 1:
        await interaction.response.send_message("❌ Amount must be at least 1!", ephemeral=True)
        return
    elif amount > 100:
        await interaction.response.send_message("❌ I can only delete up to 100 messages at once!", ephemeral=True)
        return

    # Defer the response since deletion might take time
    await interaction.response.defer(ephemeral=True)

    try:
        # Delete messages (this gets the last X messages in the channel)
        deleted = await interaction.channel.purge(limit=amount)

        # Send confirmation (ephemeral so only the user sees it)
        await interaction.followup.send(f"✅ Successfully deleted {len(deleted)} message(s)!", ephemeral=True)

    except discord.Forbidden:
        await interaction.followup.send("❌ I don't have permission to delete messages in this channel!", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.followup.send(f"❌ An error occurred: {e}", ephemeral=True)


# Clear messages command (prefix version)
@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear_prefix(ctx, amount: int):
    """Delete a specified number of messages (requires Manage Messages permission)"""

    # Validate amount
    if amount < 1:
        await ctx.send("❌ Amount must be at least 1!")
        return
    elif amount > 100:
        await ctx.send("❌ I can only delete up to 100 messages at once!")
        return

    try:
        # Delete messages (including the command message)
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message

        # Send confirmation (will be deleted after 5 seconds)
        confirmation = await ctx.send(f"✅ Successfully deleted {len(deleted) - 1} message(s)!")
        await confirmation.delete(delay=5)

    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages in this channel!")
    except discord.HTTPException as e:
        await ctx.send(f"❌ An error occurred: {e}")


# Handle permission errors for prefix command
@clear_prefix.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to delete messages!")


# Role management commands using command groups
class RoleCommands(discord.app_commands.Group):
    def __init__(self):
        super().__init__(name='role', description='Role management commands')

    @discord.app_commands.command(name='add', description='Add a role to a user')
    async def add_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        """Add a role to a user"""
        # Check if user has manage roles permission
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You don't have permission to manage roles!", ephemeral=True)
            return

        # Check if bot has manage roles permission
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ I don't have permission to manage roles!", ephemeral=True)
            return

        # Check if the role is higher than bot's highest role
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "❌ I can't manage this role because it's higher than my highest role!", ephemeral=True)
            return

        # Check if the role is higher than the user's highest role (unless they're admin)
        if not interaction.user.guild_permissions.administrator and role >= interaction.user.top_role:
            await interaction.response.send_message(
                "❌ You can't manage this role because it's higher than your highest role!", ephemeral=True)
            return

        # Check if user already has the role
        if role in user.roles:
            await interaction.response.send_message(f"❌ {user.mention} already has the **{role.name}** role!",
                                                    ephemeral=True)
            return

        try:
            await user.add_roles(role)
            await interaction.response.send_message(f"✅ Added role **{role.name}** to {user.mention}!", ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to manage this role!", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)

    @discord.app_commands.command(name='remove', description='Remove a role from a user')
    async def remove_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        """Remove a role from a user"""
        # Check if user has manage roles permission
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You don't have permission to manage roles!", ephemeral=True)
            return

        # Check if bot has manage roles permission
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ I don't have permission to manage roles!", ephemeral=True)
            return

        # Check if the role is higher than bot's highest role
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "❌ I can't manage this role because it's higher than my highest role!", ephemeral=True)
            return

        # Check if the role is higher than the user's highest role (unless they're admin)
        if not interaction.user.guild_permissions.administrator and role >= interaction.user.top_role:
            await interaction.response.send_message(
                "❌ You can't manage this role because it's higher than your highest role!", ephemeral=True)
            return

        # Check if user doesn't have the role
        if role not in user.roles:
            await interaction.response.send_message(f"❌ {user.mention} doesn't have the **{role.name}** role!",
                                                    ephemeral=True)
            return

        try:
            await user.remove_roles(role)
            await interaction.response.send_message(f"✅ Removed role **{role.name}** from {user.mention}!",
                                                    ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to manage this role!", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)


# Prefix versions (kept separate for clarity)
@bot.command(name='addrole')
@commands.has_permissions(manage_roles=True)
async def add_role_prefix(ctx, user: discord.Member, role: discord.Role):
    """Add a role to a user. Usage: !addrole @user @role"""

    # Check if bot has manage roles permission
    if not ctx.guild.me.guild_permissions.manage_roles:
        await ctx.send("❌ I don't have permission to manage roles!")
        return

    # Check role hierarchy
    if role >= ctx.guild.me.top_role:
        await ctx.send("❌ I can't manage this role because it's higher than my highest role!")
        return

    if not ctx.author.guild_permissions.administrator and role >= ctx.author.top_role:
        await ctx.send("❌ You can't manage this role because it's higher than your highest role!")
        return

    # Check if user already has the role
    if role in user.roles:
        await ctx.send(f"❌ {user.mention} already has the **{role.name}** role!")
        return

    try:
        await user.add_roles(role)
        await ctx.send(f"✅ Added role **{role.name}** to {user.mention}!")

    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to manage this role!")
    except discord.HTTPException as e:
        await ctx.send(f"❌ An error occurred: {e}")


@bot.command(name='removerole')
@commands.has_permissions(manage_roles=True)
async def remove_role_prefix(ctx, user: discord.Member, role: discord.Role):
    """Remove a role from a user. Usage: !removerole @user @role"""

    # Check if bot has manage roles permission
    if not ctx.guild.me.guild_permissions.manage_roles:
        await ctx.send("❌ I don't have permission to manage roles!")
        return

    # Check role hierarchy
    if role >= ctx.guild.me.top_role:
        await ctx.send("❌ I can't manage this role because it's higher than my highest role!")
        return

    if not ctx.author.guild_permissions.administrator and role >= ctx.author.top_role:
        await ctx.send("❌ You can't manage this role because it's higher than your highest role!")
        return

    # Check if user doesn't have the role
    if role not in user.roles:
        await ctx.send(f"❌ {user.mention} doesn't have the **{role.name}** role!")
        return

    try:
        await user.remove_roles(role)
        await ctx.send(f"✅ Removed role **{role.name}** from {user.mention}!")

    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to manage this role!")
    except discord.HTTPException as e:
        await ctx.send(f"❌ An error occurred: {e}")


# Handle permission errors for role commands
@add_role_prefix.error
async def add_role_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to manage roles!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ User not found! Make sure to mention them or use their exact username.")
    elif isinstance(error, commands.RoleNotFound):
        await ctx.send("❌ Role not found! Make sure to mention the role or use its exact name.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing arguments! Usage: `!addrole @user @role`")


@remove_role_prefix.error
async def remove_role_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to manage roles!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ User not found! Make sure to mention them or use their exact username.")
    elif isinstance(error, commands.RoleNotFound):
        await ctx.send("❌ Role not found! Make sure to mention the role or use its exact name.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing arguments! Usage: `!removerole @user @role`")


# Slash version of approve command
@bot.tree.command(name='approve', description='Approve a user and give them member roles')
async def approve_slash(interaction: discord.Interaction, discord_id: str):
    """Approve a user by their Discord ID and give them member roles"""

    # Check if user has manage roles permission
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ You don't have permission to approve users!", ephemeral=True)
        return

    # Check if bot has manage roles permission
    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ I don't have permission to manage roles!", ephemeral=True)
        return

    try:
        # Convert Discord ID to integer and get the user
        user_id = int(discord_id.strip())
        user = interaction.guild.get_member(user_id)

        if user is None:
            await interaction.response.send_message(
                "❌ User not found! Make sure they're in this server and the ID is correct.", ephemeral=True)
            return

        # Find the required roles
        member_role = discord.utils.get(interaction.guild.roles, name="The Town Bar/Grill Member")
        job_role = discord.utils.get(interaction.guild.roles, name="The Town Bar/Grill | Needs Job")

        # Check if roles exist
        missing_roles = []
        if member_role is None:
            missing_roles.append("The Town Bar/Grill Member")
        if job_role is None:
            missing_roles.append("The Town Bar/Grill | Needs Job")

        if missing_roles:
            await interaction.response.send_message(
                f"❌ Missing roles: {', '.join(missing_roles)}\nPlease create these roles first!", ephemeral=True)
            return

        # Check role hierarchy
        roles_to_add = [member_role, job_role]
        high_roles = []
        for role in roles_to_add:
            if role >= interaction.guild.me.top_role:
                high_roles.append(role.name)

        if high_roles:
            await interaction.response.send_message(
                f"❌ I can't manage these roles because they're higher than my highest role: {', '.join(high_roles)}",
                ephemeral=True)
            return

        # Add the roles
        roles_added = []
        roles_already_had = []

        for role in roles_to_add:
            if role not in user.roles:
                await user.add_roles(role)
                roles_added.append(role.name)
            else:
                roles_already_had.append(role.name)

        # Create response message
        embed = discord.Embed(title="✅ User Approved!", color=0x00ff00)
        embed.add_field(name="User", value=f"{user.mention} ({user.display_name})", inline=False)

        if roles_added:
            embed.add_field(name="Roles Added", value="\n".join(f"• {role}" for role in roles_added), inline=False)

        if roles_already_had:
            embed.add_field(name="Already Had", value="\n".join(f"• {role}" for role in roles_already_had),
                            inline=False)

        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"Approved by {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    except ValueError:
        await interaction.response.send_message("❌ Invalid Discord ID! Please enter a valid numeric Discord ID.",
                                                ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to manage these roles!", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)


# Prefix version of approve command
@bot.command(name='approve')
@commands.has_permissions(manage_roles=True)
async def approve_prefix(ctx, discord_id: str):
    """Approve a user by their Discord ID. Usage: !approve 123456789012345678"""

    # Check if bot has manage roles permission
    if not ctx.guild.me.guild_permissions.manage_roles:
        await ctx.send("❌ I don't have permission to manage roles!")
        return

    try:
        # Convert Discord ID to integer and get the user
        user_id = int(discord_id.strip())
        user = ctx.guild.get_member(user_id)

        if user is None:
            await ctx.send("❌ User not found! Make sure they're in this server and the ID is correct.")
            return

        # Find the required roles
        member_role = discord.utils.get(ctx.guild.roles, name="The Town Bar/Grill Member")
        job_role = discord.utils.get(ctx.guild.roles, name="The Town Bar/Grill | Needs Job")

        # Check if roles exist
        missing_roles = []
        if member_role is None:
            missing_roles.append("The Town Bar/Grill Member")
        if job_role is None:
            missing_roles.append("The Town Bar/Grill | Needs Job")

        if missing_roles:
            await ctx.send(f"❌ Missing roles: {', '.join(missing_roles)}\nPlease create these roles first!")
            return

        # Check role hierarchy
        roles_to_add = [member_role, job_role]
        high_roles = []
        for role in roles_to_add:
            if role >= ctx.guild.me.top_role:
                high_roles.append(role.name)

        if high_roles:
            await ctx.send(
                f"❌ I can't manage these roles because they're higher than my highest role: {', '.join(high_roles)}")
            return

        # Add the roles
        roles_added = []
        roles_already_had = []

        for role in roles_to_add:
            if role not in user.roles:
                await user.add_roles(role)
                roles_added.append(role.name)
            else:
                roles_already_had.append(role.name)

        # Create response message
        embed = discord.Embed(title="✅ User Approved!", color=0x00ff00)
        embed.add_field(name="User", value=f"{user.mention} ({user.display_name})", inline=False)

        if roles_added:
            embed.add_field(name="Roles Added", value="\n".join(f"• {role}" for role in roles_added), inline=False)

        if roles_already_had:
            embed.add_field(name="Already Had", value="\n".join(f"• {role}" for role in roles_already_had),
                            inline=False)

        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"Approved by {ctx.author.display_name}")

        await ctx.send(embed=embed)

    except ValueError:
        await ctx.send("❌ Invalid Discord ID! Please enter a valid numeric Discord ID.")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to manage these roles!")
    except discord.HTTPException as e:
        await ctx.send(f"❌ An error occurred: {e}")


# Handle permission errors for approve command
@approve_prefix.error
async def approve_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to approve users!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing Discord ID! Usage: `!approve 123456789012345678`")


# Command with user info
@bot.command(name='userinfo')
async def user_info(ctx, member: discord.Member = None):
    """Get info about a user"""
    if member is None:
        member = ctx.author

    embed = discord.Embed(title=f"User Info - {member}", color=0x00ff00)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

    await ctx.send(embed=embed)


# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found! Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument! Check the command usage.")
    else:
        await ctx.send(f"An error occurred: {error}")


# Add the role command group to the bot
role_group = RoleCommands()
bot.tree.add_command(role_group)

# Get token from environment variable
TOKEN = os.getenv('DISCORD_TOKEN')

# Check if token was loaded properly
if TOKEN is None:
    print("Error: DISCORD_TOKEN not found in environment variables!")
    print("Make sure you have a .env file with: DISCORD_TOKEN=your_bot_token")
    exit()

# Run the bot
bot.run(TOKEN)
