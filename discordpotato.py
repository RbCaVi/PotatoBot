import discord
import json

'''helpmessage="""Help:
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
> > Processes some letter substitutions for checking for potato"""'''

punishmentchannelnames=['punishments']
punishmentnotificationchannelnames=['punishment-list']

peasantroleid=1000479869823619232
newmembernotificationroleid=1018253249901514752
potatologid=1019662675480948756

invitesdict = {}

invitersdict={}

class MyClient(discord.Client):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.commands={}
        self.commandlimits={}
        self.aliases={}

    async def on_ready(self):
        print('Logged on as', self.user)
        # Getting all the guilds our bot is in
        for guild in self.guilds:
            await guild.get_channel(potatologid).send('PotatoBot is running')
            # Adding each guild's invites to our dict
            invitesdict[guild.id] = await guild.invites()

    async def on_message(self, message):
        # don't respond to ourselves
        print(message.content)
        if self.has_potato(message):
            await message.add_reaction('🥔')
        if self.is_forbidden(message):
            if message.channel.id!=potatologid:
                await message.guild.get_channel(potatologid).send('Deleted '+message.content+' by '+member_str(message.author))
                await message.delete()
                return
        if message.author == self.user:
            return
        channel=message.channel
        commandline=message.content.lower().split()
        command=commandline[0]
        if command[0]=='!':
            if command[1:] in self.commands:
                await message.guild.get_channel(potatologid).send(command+' used by '+member_str(message.author)+' with args \n'+message.content)
                await self.commands[command[1:]](self,message,channel,commandline)
                return
            elif command[1:] in self.aliases:
                await message.guild.get_channel(potatologid).send(command+' used by '+member_str(message.author)+' with args \n'+message.content)
                await self.commands[self.aliases[command[1:]]](self,message,channel,commandline)
                return
            await message.guild.get_channel(potatologid).send(command+' used by '+member_str(message.author)+' with args \n'+message.content+'\ndoes not exist')

    async def on_message_edit(self, m_before, m_after):
        this_user = m_after.channel.guild.get_member(self.user.id)
        print(m_before.content, m_after.content)
        if self.has_potato(m_after):
            await m_after.add_reaction('🥔')
        if not self.has_potato(m_after):
            await m_after.remove_reaction('🥔',this_user)
        if self.is_forbidden(m_after):
            await m_after.guild.get_channel(potatologid).send('Deleted '+m_after.content+' by '+member_str(m_after.author))
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
                # the name, invite code used, the person
                # who created the invite code, or the inviter.

                print(f"Member {member.name+'#'+member.discriminator} Joined")
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
                update_invite_roles(invitersdict,invite.inviter)

                # We will now update our cache so it's ready
                # for the next user that joins the guild

                invitesdict[member.guild.id] = invites_after_join

                # return since we already found which one was used
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

    async def makehelp(self,channel):
        print('making help message')
        helpstr=''
        print(self.commands)
        for command in self.commands:
            print(command,self.commandlimits)
            if command in self.commandlimits:
                print('limit?')
                print(channel.id)
                if channel.id not in self.commandlimits[command]:
                    print(command,'skipped')
                    continue
            print('!')
            helpstr+='> !'
            print('cmd')
            helpstr+=command
            print('aliases')
            aliases=[alias for alias in self.aliases if self.aliases[alias]==command]
            helpstr+=('\n> > Aliases: '+' '.join(aliases)) if len(aliases)>0 else ''
            print('>')
            helpstr+='\n> > '
            print('doc')
            helpstr+=(self.commands[command].__doc__ or '').replace('\n','\n> > ').split('\n')[0]
            print('newline')
            helpstr+='\n'
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

def update_invite_roles(inviters,inviter):
    invitedpeople=len(inviters[inviter.id])
    for i,rank in enumerate(config["invite-ranks"]):
        if invitedpeople==rank:
            prev_role=inviter.guild.get_role(config["invite-roles"][i-1])
            new_role=inviter.guild.get_role(config["invite-roles"][i])
            inviter.remove_roles(prev_role,reason=f'For inviting {invitedpeople} people')
            inviter.add_roles(new_role,reason=f'For inviting {invitedpeople} people')


def member_str(member):
    return "<@"+str(member.id)+">"
    return member.name+"#"+member.discriminator

def member_id_str(memberid,guild):
    member=guild.get_member(memberid)
    if member is None:
        return "<@"+str(memberid)+">"
    return "<@"+str(memberid)+">"
    return member.name+"#"+member.discriminator

def get_name(member):
    return member.nick or member.name

async def send_big_message(message,channel):
    part=''
    for line in message.split("\n"):
        if len(part)+len(line)+1>2000:
            await channel.send(part)
            part=line
            continue
        part+='\n'+line
    await channel.send(part)

def command(client,*,allowedchannels=None,aliases=None):
    def add_command(func):
        if allowedchannels is not None: # if this command is limited to certain channels
            async def func2(self,message,channel,commandline): # define a new function that will only work in the allowed channels
                if message.channel.id not in allowedchannels:
                    print("not allowed")
                    return
                await func(self,message,channel,commandline)
            func2.__doc__=func.__doc__
            client.commands[func.__name__]=func2
            client.commandlimits[func.__name__]=allowedchannels
        else:
            client.commands[func.__name__]=func
        if aliases is not None:
            for alias in aliases:
                client.aliases[alias]=func.__name__
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
    "Check if PotatoBot is running"
    await channel.send("Pong!")

@command(client)
async def echo(self,message,channel,commandline):
    "Echo a message"
    await channel.send(message.content.split(maxsplit=1)[1])

@command(client)
async def say(self,message,channel,commandline):
    "Say a message"
    await message.guild.get_channel(potatologid).send('Deleted '+message.content+' by '+member_str(message.author))
    await message.delete()
    await channel.send(message.content.split(maxsplit=1)[1],reference=message.reference)

@command(client)
async def help(self,message,channel,commandline):
    "Show this help message"
    #await channel.send(helpmessage)
    print('making help message')
    madehelp=await self.makehelp(channel)
    await channel.send(madehelp)

@command(client)
async def help_roles(self,message,channel,commandline):
    "Show the roles that can be toggled and/or managed"
    roleids=[str(role.id) for role in message.author.roles]
    selftoggleroles='\n'.join(['> `@'+channel.guild.get_role(role).name+'`' for role in config["role-add-any"]])
    print([config["manage-role-ids"][roleid] for roleid in config["manage-role-ids"] if roleid in roleids])
    managedroleids=sum([config["manage-role-ids"][roleid] for roleid in config["manage-role-ids"] if roleid in roleids],[])
    print(managedroleids)
    managedroles='\n'.join(['> `@'+channel.guild.get_role(role).name+'`'
        for role in
        managedroleids
    ])
    print(managedroles)
    finalmessage=(f'<@{message.author.id}> can manage roles:\n{managedroles}\n\n' if len(managedroleids)>0 else '')+f'Anyone can toggle roles:\n{selftoggleroles}'
    await channel.send(finalmessage)

@command(client)
async def users(self,message,channel,commandline):
    "Print a list of all the users in the server, sorted by name"
    users=message.guild.members
    await channel.send('\n'.join([
        "<@"+str(mem.id)+">"
        for mem in sorted(message.guild.members,key=lambda x:get_name(x))
    ]))

@command(client,allowedchannels=[1000563661921857557])
async def invited(self,message,channel,commandline):
    "DO NOT USE!\nManually add someone to the invited list by ID"
    inviterid=int(commandline[1])
    memberid=int(commandline[2])
    if memberid not in invitersdict:
        invitersdict[memberid]=[]
    if memberid not in invitersdict[inviterid]:
        invitersdict[inviterid].append(memberid)
    write_inviters(invitersdict)
    update_invite_roles(invitersdict,message.guild.get_member(inviterid))

@command(client)
async def inviters(self,message,channel,commandline):
    "Print a list of all the users in the server and the people they invited, sorted by number of invites"
    guild=channel.guild
    if len(message.mentions)==0:
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
    else:
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
            for inviter in [mention.id for mention in message.mentions]
        ],key=lambda x:len([l for l in x if l=='\n']))))
    print(invitersmessage)
    await send_big_message(invitersmessage,channel)

@command(client)
async def invites(self,message,channel,commandline):
    "Print a list of all the invites to this server"
    invites=await message.guild.invites()
    invites=[
        member_str(invite.inviter)+": https://discord.gg/"+invite.code
        for invite in invites
    ]
    await channel.send('\n'.join(invites))

@command(client)
async def giverole(self,message,channel,commandline):
    "Give a role to someone"
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
    "Remove a role from someone"
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
    "Toggle a role"
    roles=message.author.roles
    if message.role_mentions[0].id in config["role-add-any"]:
        for role in roles:
            if role.id==message.role_mentions[0].id:
                await message.author.remove_roles(message.role_mentions[0])
                successmessage='`@'+message.role_mentions[0].name+'` role has been toggled off for '+get_name(message.author)
                await channel.send(successmessage)
                return
        await message.author.add_roles(message.role_mentions[0])
        successmessage='`@'+message.role_mentions[0].name+'` role has been toggled on for '+get_name(message.author)
        await channel.send(successmessage)
        return
    failmessage='You do not have permission to toggle `@'+message.role_mentions[0].name+'`'
    await channel.send(failmessage)

@command(client)
async def kick(self,message,channel,commandline):
    "Kick someone from the server"
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
    "Ban someone from the server"
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

@command(client,allowedchannels=[1000563661921857557])
async def reconfig(self,message,channel,commandline):
    "Reload the config file"
    with open("config.json","r") as configfile:
        config = json.loads(configfile.read())

print("Initialized client")

with open("config.json","r") as configfile:
    config = json.loads(configfile.read())

print('Read token')
client.run(token)
