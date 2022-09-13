import discord
import json

helpmessage="""Help:
> Commands:
> !ping
> > Check if PotatoBot is running
> !help
> > Show this help message
> !users
> > Print a list of all the users in the server, sorted by name
Punishment commands:
> !kick
> > Kick a user from the server (only works in a channel named punishments)
> !ban
> > Ban a user from the server (only works in a channel named punishments)
> Other stuff:
> > Adds the '🥔' reaction to any message containing potato
> > Deletes any message containing the name or emoji of the forbidden vegetable
> > Processes some letter substitutions for checking for potato"""

punishmentchannelnames=['punishments']
punishmentnotificationchannelnames=['punishment-list']

peasantroleid=1000479869823619232
newmembernotificationroleid=1018253249901514752

invitesdict = {}

invitersdict={}

class MyClient(discord.Client):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.commands={}
        self.commandlimits={}

    async def on_ready(self):
        print('Logged on as', self.user) 
        # Getting all the guilds our bot is in
        for guild in self.guilds:
            # Adding each guild's invites to our dict
            invitesdict[guild.id] = await guild.invites()

    async def on_message(self, message):
        # don't respond to ourselves
        print(message.content)
        if message.author == self.user:
            return
        channel=message.channel
        commandline=message.content.lower().split()
        command=commandline[0]
        if self.has_potato(message):
            await message.add_reaction('🥔')
        if self.is_forbidden(message):
            await message.delete()
            return
        if command[0]=='!':
            try:
                if command[1:] not in self.commands:
                    return
                await self.commands[command[1:]](self,message,channel,commandline)
            except NameError:
                pass

    async def on_message_edit(self, m_before, m_after):
        this_user = m_after.channel.guild.get_member(self.user.id)
        print(m_before.content, m_after.content)
        if self.has_potato(m_after):
            await m_after.add_reaction('🥔')
        if not self.has_potato(m_after):
            await m_after.remove_reaction('🥔',this_user)
        if self.is_forbidden(m_after):
            await m_after.delete()

    async def on_member_update(self, m_before, m_after):
        pass

    async def on_member_join(self, member):
        print("a member joined!")
        welcome_channel=member.guild.get_channel(1000561459266326588)
        print(member,welcome_channel)
        await welcome_channel.send("<@&"+str(newmembernotificationroleid)+"> welcome the newest member of this server <@"+str(member.id)+">!")
        await member.add_roles(member.guild.get_role(peasantroleid),reason="on join")

        # Getting the invites before and after the user joined so we can compare them and
        # see which invite's uses increased
        invites_before_join = invitesdict[member.guild.id]
        invites_after_join = await member.guild.invites()

        # Loop over each invite we have for the guild
        # the user joined.

        for invite in invites_before_join:
            # check if this invite has been used
            if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses:
                
                # Now that we found which link was used,
                # we will print a couple things in our console:
                # the name, invite code used, the the person
                # who created the invite code, or the inviter.
                
                #print(f"Member {(member.name+"#"+member.discriminator)} Joined")
                print(f"Invite Code: {invite.code}")
                print(f"Inviter: {invite.inviter}")
                print(f"Member {member.id} Joined")
                print(f"Inviter: {invite.inviter.id}")
                
                # add an entry for the member in inviters.txt and the inviters variable
                if member.id not in invitersdict:
                    invitersdict[member.id]=[]
                if member.id not in invitersdict[invite.inviter.id]:
                    invitersdict[invite.inviter.id].append(member.id)
                write_inviters(invitersdict)

                # We will now update our cache so it's ready
                # for the next user that joins the guild

                invitesdict[member.guild.id] = invites_after_join
                
                # We return here since we already found which 
                # one was used and there is no point in
                # looping when we already got what we wanted
                return

    def has_potato(self,message):
        processed_message=process(message.content)
        return 'potat' in processed_message or '🥔' in processed_message

    def is_forbidden(self,message):
        processed_message=process(message.content)
        for forbidden in [
            '\x63\x61\x72\x72\x6f\x74',
            '\x63\x61\x72\x6f\x74',
            '\x63\x61\x72\x72\x61\x74',
            '\x63\x61\x72\x61\x74',
            '\xf0\x9f\xa5\x95'
        ]:
            if forbidden in processed_message:
                return True
        return False

    async def on_member_remove(self,member):
        # Update the cache when a user leaves to make sure everything is up to date
        invitesdict[member.guild.id] = await member.guild.invites()

    def makehelp(self,channel):
        helpstr=''
        for command in self.commands:
            if channel.id not in commandlimits[command]:
                continue
            helpstr+='> !'+command+'\n> > '+(self.commands[command].__doc__ or '').replace('\n','\n> > ')+'\n'
        return helpstr

def process(message):
    replacements={
        "o":['0'],
        "a":['4','@'],
        "":['\n',' '],
    }
    processed_message=message
    repl={}
    for r in replacements:
        ps=replacements[r]
        for p in ps:
            repl[p]=r
    for p in repl:
        r=repl[p]
        processed_message=processed_message.replace(p,r)
    return processed_message

def find_invite_by_code(invite_list, code):
    # get the invite from invite_list with code
    
    for inv in invite_list:
        if inv.code == code:
            return inv

def read_inviters():
    with open('inviters.txt','r') as file:
        inviters=file.read().split('\n')
    inviters={int(x.split()[0]):[*map(int,x.split()[1:])] for x in filter(lambda x:x!='',inviters)}
    return inviters

def write_inviters(inviters):
    with open('inviters.txt','w') as file:
        for inviter in inviters:
            file.write(str(inviter)+" "+" ".join([str(invited) for invited in inviters[inviter]])+"\n")

def member_str(member):
    return "<@"+str(member.id)+">"
    return member.name+"#"+member.discriminator

def member_id_str(memberid,guild):
    member=guild.get_member(memberid)
    if member is None:
        return "<@"+str(memberid)+">"
    return "<@"+str(memberid)+">"
    return member.name+"#"+member.discriminator

def command(client,*,allowedchannels=None):
    def add_command(func):
        if allowedchannels is not None: # if this command is limited to certain channels
            async def func2(self,message,channel,commandline): # define a new function that will only work in the limited channels
                if message.channel.id not in allowedchannels:
                    print("not allowed")
                    return
                await func(self,message,channel,commandline)
            func2.__doc__=func.__doc__
            client.commands[func.__name__]=func2
        else:
            client.commands[func.__name__]=func
    return add_command

print('Starting...')

intents = discord.Intents.all()

with open("token","r") as tokenfile:
    token = tokenfile.read()

invitersdict=read_inviters()

intents = discord.Intents.all()

client = MyClient(intents=intents)

@command(client)
async def ping(self,message,channel,commandline):
    """Check if PotatoBot is running"""
    await channel.send("Pong!")

@command(client)
async def help(self,message,channel,commandline):
    """Show this help message"""
    await channel.send(helpmessage)
    await channel.send(self.makehelp())

@command(client)
async def help_roles(self,message,channel,commandline):
    """Show the roles that can be toggled"""
    await channel.send(helpmessage)
    await channel.send(self.makehelp())

@command(client)
async def users(self,message,channel,commandline):
    """Print a list of all the users in the server, sorted by name"""
    users=message.guild.members
    await channel.send('\n'.join([
        "<@"+str(mem.id)+">" 
        for mem in sorted(message.guild.members,key=lambda x:x.nick or x.name)
    ]))

@command(client,allowedchannels=[1000563661921857557])
async def invited(self,message,channel,commandline):
    """DO NOT USE!
    Manually add someone to the invited list"""
    inviterid=int(commandline[1])
    memberid=int(commandline[2])
    if memberid not in invitersdict:
        invitersdict[memberid]=[]
    if memberid not in invitersdict[inviterid]:
        invitersdict[inviterid].append(memberid)
    write_inviters(invitersdict)

@command(client)
async def inviters(self,message,channel,commandline):
    """Print a list of all the users in the server and the people they invited, sorted by number of invites"""
    guild=channel.guild
    invitersmessage=('\n'.join(sorted([
        (
            member_id_str(inviter,guild)+
            ":"+
            ''.join([
                '\n> '+member_id_str(inviter2,guild)
                for inviter2 in invitersdict[inviter]
            ])+
            "\n"
        ).strip()+'\n'
        for inviter in invitersdict
    ],key=lambda x:len([l for l in x if l=='\n']))))
    print(invitersmessage)
    m=''
    for invs in invitersmessage.split("\n"):
        if len(m)+len(invs)+1>2000:
            await channel.send(m)
            m=invs
        m+='\n'+invs
    await channel.send(m)

@command(client)
async def invites(self,message,channel,commandline):
    """Print a list of all the invites to this server"""
    invites=await message.guild.invites()
    invites=[
        member_str(invite.inviter)+": https://discord.gg/"+invite.code 
        for invite in invites
    ]
    await channel.send('\n'.join(invites))

@command(client)
async def giverole(self,message,channel,commandline):
    """Give a role to someone"""
    roles=message.author.roles
    for role in roles:
        if str(role.id) in config["manage-role-ids"]:
            if message.role_mentions[0].id in config["manage-role-ids"][str(role.id)]:
                if len(commandline)>3:
                    reason=' '.join(commandline[3:])
                else:
                    reason=None
                await message.mentions[0].add_roles(message.role_mentions[0],reason=reason)
                successmessage='The `@'+message.role_mentions[0].name+'` role has successfully been given to '+member_str(message.mentions[0])+' '+reason
                await channel.send(successmessage)
                return
    failmessage='You do not have permission to give `@'+message.role_mentions[0].name+'` to '+member_str(message.mentions[0])
    await channel.send(failmessage)

@command(client)
async def removerole(self,message,channel,commandline):
    """Remove a role from someone"""
    roles=message.author.roles
    for role in roles:
        if str(role.id) in config["manage-role-ids"]:
            if message.role_mentions[0].id in config["manage-role-ids"][str(role.id)]:
                if len(commandline)>3:
                    reason=' '.join(commandline[3:])
                else:
                    reason=None
                await message.mentions[0].remove_roles(message.role_mentions[0],reason=reason)
                successmessage='The `@'+message.role_mentions[0].name+'` role has successfully been removed from '+member_str(message.mentions[0])+' '+reason
                await channel.send(successmessage)
                return
    failmessage='You do not have permission to remove `@'+message.role_mentions[0].name+'` from '+member_str(message.mentions[0])
    await channel.send(failmessage)

@command(client)
async def togglerole(self,message,channel,commandline):
    """Toggle a role"""
    roles=message.author.roles
    if str(message.role_mentions[0].id) in config["role-add-any"]:
        for role in roles:
            if role.id==message.role_mentions[0].id:
                message.author.remove_roles(message.role_mentions[0])
                return
        message.author.add_roles(message.role_mentions[0])
    failmessage='You do not have permission to toggle `@'+message.role_mentions[0].name+'`'
    await channel.send(failmessage)

@command(client)
async def kick(self,message,channel,commandline):
    """Kick someone from the server"""
    if channel.name!='punishments':
        return
    userstr = commandline[1]
    reason = " ".join(commandline[2:])
    if reason.split()==[]:
        reason="for no reason"
    print(message.mentions[0])
    user=message.mentions[0]
    await channel.guild.kick(user,reason=reason)
    await channel.send("Kicked "+userstr+"\nReason: "+reason)
    punishment_channel = channel.guild.get_channel(1000561797557932134)
    await punishment_channel.send("Kicked "+userstr+"\nReason: "+reason)

@command(client)
async def ban(self,message,channel,commandline):
    """Ban someone from the server"""
    if channel.name!='punishments':
        return
    userstr = commandline[1]
    reason = " ".join(commandline[2:])
    if reason.split()==[]:
        reason="for no reason"
    print(message.mentions[0])

    user=message.mentions[0]
    await channel.guild.ban(user,reason=reason)

    banmessage="Banned "+userstr+"\nReason: "+reason
    await channel.send(banmessage)

    punishment_channel = channel.guild.get_channel(1000561797557932134)
    await punishment_channel.send(banmessage)

@command(client)
async def reconfig(self,message,channel,commandline):
    """Reload the config file"""
    with open("config.json","r") as configfile:
        config = json.loads(configfile.read())

print("Initialized client")

with open("config.json","r") as configfile:
    config = json.loads(configfile.read())

print('Read token')
client.run(token)
