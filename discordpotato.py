import discord
import json

invitesdict = {}

invitersdict={}

class MyClient(discord.Client):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.commands={}
        self.commandlimits={}
        self.aliases={}
        self.commandargs={'example':[['arg1','string','The first argument']]}

    async def on_ready(self):
        print('Logged on as', self.user)
        # Getting all the guilds our bot is in
        for guild in self.guilds:
            await guild.get_channel(allconfig[str(guild.id)]['potato-log']).send('PotatoBot is running')
            # Adding each guild's invites to our dict
            invitesdict[guild.id] = await guild.invites()
            if guild.id not in invitersdict:
                invitersdict[guild.id]={}
                for user in guild.members:
                    invitersdict[guild.id][user.id]=[]

    async def on_message(self, message):
        # don't respond to ourselves
        print(message.content)
        if self.has_potato(message):
            await message.add_reaction('🥔')
        if self.is_forbidden(message):
            if message.channel.id!=allconfig[str(message.guild.id)]['potato-log']:
                await log(message,'Deleted '+message.content+' by '+member_str(message.author))
                await message.delete()
                return
        if message.author == self.user:
            return
        channel=message.channel
        commandline=message.content.lower().split()
        command=commandline[0]
        config=allconfig[str(message.guild.id)]
        if command[0]=='!':
            await self.run_command(message,channel,commandline,config,command[1:])

    async def run_command(self,message,channel,commandline,config,command):
            if command in self.commands:
                await log(message,command+' used by '+member_str(message.author)+' with args \n'+message.content)
                await self.commands[command](self,message,channel,commandline,config)
                return
            elif command in self.aliases:
                await self.run_command(message,channel,commandline,config,self.aliases[command])
                return
            await log(message,command+' used by '+member_str(message.author)+' with args \n'+message.content+'\ndoes not exist')


    async def on_message_edit(self, m_before, m_after):
        this_user = m_after.channel.guild.get_member(self.user.id)
        print(m_before.content, m_after.content)
        if self.has_potato(m_after):
            await m_after.add_reaction('🥔')
        if not self.has_potato(m_after):
            await m_after.remove_reaction('🥔',this_user)
        if self.is_forbidden(m_after):
            await log(m_after,'Deleted '+m_after.content+' by '+member_str(m_after.author))
            await m_after.delete()

    async def on_member_update(self, m_before, m_after):
        pass

    async def on_member_join(self, member):
        config=allconfig[str(member.guild.id)]
        print("a member joined!")
        welcome_channel=member.guild.get_channel(config['welcome-channel'])
        print(member,welcome_channel)
        await welcome_channel.send("<@&"+str(config['new-member-notification-role'])+"> welcome the newest member of this server <@"+str(member.id)+">!")

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

                # add an entry for the member in inviters.json and the inviters variable
                inviters=invitersdict[member.guild.id]
                if member.id not in inviters:
                    inviters[member.id]=[]
                if member.id not in inviters[invite.inviter.id]:
                    inviters[invite.inviter.id].append(member.id)
                write_inviters(inviters)
                await update_invite_roles(self,inviters,member.guild.get_member(invite.inviter.id),config)

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

    def makehelp(self,channel):
        helpstr=''
        for command in self.commands:
            if command in self.commandlimits:
                if channel.id not in self.commandlimits[command]:
                    continue
            aliases=[alias for alias in self.aliases if self.aliases[alias]==command]
            helpstr+=(
                '> !'+
                command+self.getargs(command)+
                (('\n> > Aliases: '+' '.join(aliases)) if len(aliases)>0 else '')+
                '\n> > '+
                (self.commands[command].__doc__ or '').split('\n')[0]+
                '\n'
            )
        return helpstr

    def makecommandhelp(self,channel,command):
        if command in self.commandlimits:
            if channel.id not in self.commandlimits[command]:
                return ''
        aliases=[alias for alias in self.aliases if self.aliases[alias]==command]
        if command in self.commandargs:
            args=[f'\n> > {arg[0]} ({arg[1]}) {arg[2]}' for arg in self.commandargs[command]]
        else:
            args=[]
        helpstr=(
            '> !'+
            command+self.getargs(command)+
            (('\n> > Aliases: '+' '.join(aliases)) if len(aliases)>0 else '')+
            ('\n> > Arguments:'+''.join(args) if len(args)>0 else '')+
            '\n> > '+
            (self.commands[command].__doc__ or '').replace('\n','\n> > ')
        )
        return helpstr

    def getargs(self,command):
        if command not in self.commandargs:
            return ''
        return ''.join([' '+arg[0] for arg in self.commandargs[command]])


async def log(m,message):
    await m.guild.get_channel(allconfig[str(m.guild.id)]['potato-log']).send(message)

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
    with open('inviters.json','r') as file:
        data=file.read()
    inviters=json.loads(data)
    inviters={int(guild):{int(member):inviters[guild][member] for member in inviters[guild]} for guild in inviters}
    return inviters

def write_inviters(inviters):
    print(json.dumps({str(inviter):inviters[inviter] for inviter in inviters}))
    with open('inviters.json','w') as file:
        file.write(json.dumps({guild:{str(inviter):invitersdict[guild][inviter] for inviter in invitersdict[guild]} for guild in invitersdict}))
        #for inviter in inviters:
        #    file.write(str(inviter)+" "+" ".join([str(invited) for invited in inviters[inviter]])+"\n")

async def update_invite_roles(client,inviters,inviter,config):
    invitedpeople=len(inviters[inviter.id])
    print(invitedpeople)
    for i,rank in enumerate(config["invite-ranks"]):
        if invitedpeople==rank:
            prev_role=inviter.guild.get_role(config["invite-roles"][i-1])
            new_role=inviter.guild.get_role(config["invite-roles"][i])
            await inviter.remove_roles(prev_role,reason=f'For inviting {invitedpeople} people')
            await inviter.add_roles(new_role,reason=f'For inviting {invitedpeople} people')
            await log(inviter,f'Gave {get_name(inviter)} `{new_role.name}` for inviting {invitedpeople} people')
            break


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

def get_managed_role_ids(member):
    config=allconfig[str(member.guild.id)]
    roleids=[str(role.id) for role in member.roles]
    managedroleids=sum([config["manage-role-ids"][roleid] for roleid in config["manage-role-ids"] if roleid in roleids],[])
    return sorted(set(managedroleids),key=lambda x:member.guild.get_role(x).name)

def command(client,*,allowedchannels=None,aliases=None,args=None):
    def add_command(func):
        client.commands[func.__name__]=func
        if allowedchannels is not None: # if this command is limited to certain channels
            client.commandlimits[func.__name__]=allowedchannels
        if aliases is not None:
            for alias in aliases:
                client.aliases[alias]=func.__name__
        if args is not None:
            client.commandargs[command]=args
    return add_command

print('Starting...')

intents = discord.Intents.all()

with open("token","r") as tokenfile:
    token = tokenfile.read()

invitersdict=read_inviters()

with open("config.json","r") as configfile:
    allconfig = json.loads(configfile.read())

intents = discord.Intents.all()

client = MyClient(intents=intents)

modonly=allconfig["mod-only-channels"]

@command(client)
async def ping(self,message,channel,commandline,config):
    "Check if PotatoBot is running"
    await channel.send("Pong!")

@command(client,args=[['message','string','The message to echo']])
async def echo(self,message,channel,commandline,config):
    "Echo a message"
    await channel.send(message.content.split(maxsplit=1)[1])

@command(client,args=[['message','string','The message to say']])
async def say(self,message,channel,commandline,config):
    "Say a message"
    await log(message,'Deleted '+message.content+' by '+member_str(message.author))
    await message.delete()
    await channel.send(message.content.split(maxsplit=1)[1],reference=message.reference)

@command(client,args=[['commands... ',None,'The name of commands to get help about',True]])
async def help(self,message,channel,commandline,config):
    "Show this help message"
    if len(commandline)==1:
        madehelp=self.makehelp(channel)
        await channel.send(madehelp)
    else:
        for command in commandline[1:]:
            madehelp=[]
            madehelp.append(self.makecommandhelp(channel,command))
        await channel.send('\n\n'.join(madehelp))

@command(client)
async def stats(self,message,channel,commandline,config):
    "Show some stats"
    statsmessage=f'Number of members: {len(message.guild.members)}'
    await message.channel.send('Config successfully reloaded!')

@command(client)
async def help_roles(self,message,channel,commandline,config):
    "Show the roles that can be toggled and/or managed"
    selftoggleroles='\n'.join(['> `@'+channel.guild.get_role(role).name+'`' for role in config["role-add-any"]])
    managedroleids=get_managed_role_ids(message.author)
    managedroles='\n'.join(['> `@'+channel.guild.get_role(role).name+'`'
        for role in
        managedroleids
    ])
    print(managedroles)
    finalmessage=(f'<@{message.author.id}> can manage roles:\n{managedroles}\n\n' if len(managedroleids)>0 else '')+f'Anyone can toggle roles:\n{selftoggleroles}'
    await channel.send(finalmessage)

@command(client)
async def users(self,message,channel,commandline,config):
    "Print a list of all the users in the server, sorted by name"
    users=message.guild.members
    await channel.send('\n'.join([
        "<@"+str(mem.id)+">"
        for mem in sorted(message.guild.members,key=lambda x:get_name(x))
    ]))

@command(client)
async def roles(self,message,channel,commandline,config):
    "Print a list of all the roles in the server, sorted by name"
    await channel.send('\n'.join([
        "<@&"+str(role.id)+">"
        for role in sorted(message.guild.roles,key=lambda x:x.name)
    ]))

@command(client)
async def ranks(self,message,channel,commandline,config):
    "Print a list of all the roles in the server, sorted by rank"
    await channel.send('\n'.join([
        "<@&"+str(role.id)+">"
        for role in message.guild.roles
    ]))

@command(client,allowedchannels=modonly,args=[['inviter','id','The ID of the inviter'],['invited','id','The ID of the invited member']])
async def invited(self,message,channel,commandline,config):
    "DO NOT USE!\nManually add someone to the invited list by ID"
    inviterid=int(commandline[1])
    memberid=int(commandline[2])
    inviters=invitersdict[message.guild.id]
    if memberid not in inviters:
        inviters[memberid]=[]
    if memberid not in inviters[inviterid]:
        inviters[inviterid].append(memberid)
    write_inviters(inviters)
    await update_invite_roles(self,inviters,message.guild.get_member(inviterid),config)

@command(client,args=[['inviter...','@person','The people to print the inviters for',True]])
async def inviters(self,message,channel,commandline,config):
    "Print a list of all the users in the server and the people they invited, sorted by number of invites"
    inviters=invitersdict[message.guild.id]
    guild=channel.guild
    if len(message.mentions)==0:
        invitersmessage=('\n'.join(sorted([
            (
                member_id_str(inviter,guild)+
                ":"+
                ''.join([
                    '\n> '+member_id_str(inviter2,guild)
                    for inviter2 in inviters[inviter]
                ])+
                "\n"
            ).strip()+'\n'
            for inviter in inviters
        ],key=lambda x:len([l for l in x if l=='\n']))))
    else:
        invitersmessage=('\n'.join(sorted([
            (
                member_id_str(inviter,guild)+
                ":"+
                ''.join([
                    '\n> '+member_id_str(inviter2,guild)
                    for inviter2 in inviters[inviter]
                ])+
                "\n"
            ).strip()+'\n'
            for inviter in [mention.id for mention in message.mentions]
        ],key=lambda x:len([l for l in x if l=='\n']))))
    print(invitersmessage)
    await send_big_message(invitersmessage,channel)

@command(client)
async def invites(self,message,channel,commandline,config):
    "Print a list of all the invites to this server"
    invites=await message.guild.invites()
    invites=[
        member_str(invite.inviter)+": https://discord.gg/"+invite.code
        for invite in invites
    ]
    await channel.send('\n'.join(invites))

@command(client,args=[['person','@person','The person to give the role to',True],['role','@role','The role to give',True]])
async def giverole(self,message,channel,commandline,config):
    "Give a role to someone"
    managedroleids=get_managed_role_ids(message.author)
    if message.role_mentions[0].id in managedroleids:
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

@command(client,args=[['person','@person','The person to remove the role from',True],['role','@role','The role to remove',True]])
async def removerole(self,message,channel,commandline,config):
    "Remove a role from someone"
    managedroleids=get_managed_role_ids(message.author)
    if message.role_mentions[0].id in managedroleids:
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

@command(client,args=[['role','@role','The role to toggle']])
async def togglerole(self,message,channel,commandline,config):
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

@command(client,allowedchannels=modonly,args=[['person','@person','The person to kick'],['reason','@person','The person to kick']])
async def kick(self,message,channel,commandline,config):
    "Kick someone from the server"
    if channel.id not in config['punishment-channels']:
        return
    userstr = commandline[1]
    reason = " ".join(commandline[2:])
    if reason.split()==[]:
        reason="for no reason"

    print(message.mentions[0])
    user=message.mentions[0]
    await channel.guild.kick(user,reason=reason)
    kickmessage="Kicked "+userstr+"\nReason: "+reason
    await channel.send(kickmessage)

    for channelid in config["punishment-notification-channels"]:
        punishment_channel = channel.guild.get_channel(channelid)
        await punishment_channel.send(kickmessage)

@command(client,allowedchannels=modonly,args=[['person','@person','The person to ban']])
async def ban(self,message,channel,commandline,config):
    "Ban someone from the server"
    if channel.id not in config['punishment-channels']:
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

    for channelid in config["punishment-notification-channels"]:
        punishment_channel = channel.guild.get_channel(channelid)
        await punishment_channel.send(banmessage)

@command(client,allowedchannels=modonly)
async def reconfig(self,message,channel,commandline,config):
    "Reload the config file"
    global allconfig
    with open("config.json","r") as configfile:
        allconfig = json.loads(configfile.read())
    await message.channel.send('Config successfully reloaded!')

print("Initialized client")

print('Read token')
client.run(token)
