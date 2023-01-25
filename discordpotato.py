import discord
import json
import datetime
import requests
import os
import pprint
import subprocess
import tqdm
import shutil
import sys

if os.name=='nt':
    python='py'
else:
    python='python3'

invitesdict={}

invitersdict={}

class MyClient(discord.Client):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.commands={}
        self.commandlimits={}
        self.aliases={}
        self.commandargs={'example':[['arg1','string','The first argument']]}

    async def on_ready(self):
        lock()
        logf(logfile,'Logged on as',self.user)
        # Getting all the guilds our bot is in
        for guild in self.guilds:
            if 'potato-log' in allconfig[str(guild.id)]:
                await guild.get_channel(allconfig[str(guild.id)]['potato-log']).send('PotatoBot is running')
            # Adding each guild's invites to our dict
            invitesdict[guild.id] = await guild.invites()
            if guild.id not in invitersdict:
                invitersdict[guild.id]={}
                for user in guild.members:
                    invitersdict[guild.id][user.id]=[]

    async def on_message(self, message):
        # don't respond to ourselves
        config=allconfig[str(message.guild.id)]
        logf(logfile,f'+{message.guild.id} {message.channel.id} {message.author.id} '+message.content)
        if self.has_potato(message):
            await message.add_reaction('🥔')
        if self.is_forbidden(message):
            if message.channel.id!=allconfig[str(message.guild.id)].get('potato-log',None):
                await log(message,'Deleted '+message.content+' by '+member_str(message.author))
                await message.delete()
                return
        if message.author == self.user and not config.get('self-response',False):
            return
        channel=message.channel
        commandline=message.content.lower().split()
        if len(commandline)==0:
            return
        command=commandline[0]
        if command[0]=='!':
            await self.run_command(message,channel,commandline,config,command[1:])

    async def run_command(self,message,channel,commandline,config,command):
            if command in self.commands:
                if command in config.get("command-restrictions",{}):
                    author=message.author
                    restrictions=config["command-restrictions"][command]
                    if type(restrictions)==dict:
                        restrictions=[restrictions]
                    if type(restrictions)==bool:
                        allowed=restrictions
                    elif len(restrictions)==0:
                        allowed=True
                    else:
                        allowed=False
                        for restriction in restrictions:
                            allow=True
                            if 'user' in restriction:
                                allow&=(restriction["user"].get("allow-for-all",True)^
                                (author.id in restriction["user"].get("exceptions",[])))
                            if 'channel' in restriction:
                                allow&=(restriction["channel"].get("allow-for-all",True)^
                                (message.channel.id in restriction["channel"].get("exceptions",[])))
                            allowed|=allow
                else:
                    allowed=True
                if not allowed:
                    return
                await log(message,command+' used by '+member_str(message.author)+' with args \n'+message.content)
                await self.commands[command](self,message,channel,commandline,config)
                return
            elif command in self.aliases:
                await self.run_command(message,channel,commandline,config,self.aliases[command])
                return
            await log(message,command+' used by '+member_str(message.author)+' with args \n'+message.content+'\ndoes not exist')

    async def on_message_edit(self, m_before, m_after):
        this_user = m_after.channel.guild.get_member(self.user.id)
        logf(logfile,'~'+m_before.content.replace('|','\\|')+'|'+m_after.content.replace('|','\\|'))
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
        logf(logfile,f"j{member.id}")
        if 'welcome-channel' in config:
            welcome_channel=member.guild.get_channel(config['welcome-channel'])
            if 'new-member-notification-role' in config:
                await welcome_channel.send("<@&"+str(config['new-member-notification-role'])+"> welcome the newest member of this server <@"+str(member.id)+">!")
            else:
                await welcome_channel.send("@everyone welcome the newest member of this server <@"+str(member.id)+">!")

        # Getting the invites before and after the user joined so we can compare them and
        # see which invite's uses increased
        invites_before_join = invitesdict[member.guild.id]
        invites_after_join = await member.guild.invites()

        # Loop over each invite we have for the guild
        # the user joined.

        for invite in invites_before_join:
            # check if this invite has been used
            newinvite=find_invite_by_code(invites_after_join, invite.code)
            if newinvite is None or invite.uses < newinvite.uses:

                # Now that we found which link was used,
                # we will print a couple things in our console:
                # the name, invite code used, and the inviter, or the person
                # who created the invite code.

                logf(logfile,f"#Member {member.name+'#'+member.discriminator} Joined")
                logf(logfile,f"#Invite Code: {invite.code}")
                logf(logfile,f"#Inviter: {invite.inviter}")
                logf(logfile,f"#Member {member.id} Joined")
                logf(logfile,f"#Inviter: {invite.inviter.id}")

                # add an entry for the member in inviters.json and the inviters variable
                inviters=invitersdict[member.guild.id]
                if member.id not in inviters:
                    inviters[member.id]=[]
                else:
                    await update_invite_roles(self,inviters,member.guild.get_member(member.id),config)
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
            args=[f'\n> > {arg[0]}'+(f' ({arg[1]}) ' if arg[1] is not None else ' ')+f'{arg[2]}' for arg in self.commandargs[command]]
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
        return ''.join([' '+('[' if (len(arg)>3 and arg[3]) else '<')+arg[0]+(']' if (len(arg)>3 and arg[3]) else '>') for arg in self.commandargs[command]])

def processexceptions(exceptions):
    pass
    if type(exceptions)==int:
        return [oid]
    elif type(exceptions)==str:
        ids=config.get("groups",{}).get(oid,[])
    elif type(oid)==list:
        ids=oid
    newids=[]
    for oid in ids:
        newid=processgroups(oid)
        newids+=newid
    return newids

def processgroups(config,oid):
    if type(oid)==int:
        return [oid]
    elif type(oid)==str:
        ids=config.get("groups",{}).get(oid,[])
    elif type(oid)==list:
        ids=oid
    newids=[]
    for oid in ids:
        newid=processgroups(oid)
        newids+=newid
    return newids

async def log(m,message):
    config=allconfig[str(m.guild.id)]
    if 'potato-log' in config:
        await m.guild.get_channel(config['potato-log']).send(message)

def logf(f,*message):
    for part in message:
        if type(part)==str:
            f.write(part)
        else:
            f.write(str(part))
        f.write('\n')
        f.flush()
    print(*message)

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
        inviters=json.load(file)
    inviters={
        int(guild):{
            int(member):inviters[guild][member]
            for member in inviters[guild]
        }
        for guild in inviters
    }
    return inviters

def write_inviters(inviters):
    with open('inviters.json','w') as file:
        json.dump(
            {
                guild:{
                    str(inviter):invitersdict[guild][inviter]
                    for inviter in invitersdict[guild]
                }
                for guild in invitersdict
            },
            file,
            indent=4
        )

def update_config(config):
    with open('config.json','w') as file:
        json.dump(config,file,indent=4)

async def update_invite_roles(client,inviters,inviter,config):
    invitedpeople=len(inviters[inviter.id])
    if "invite-ranks" not in config or "invite-roles" not in config:
        return
    for invitedpeoples in range(invitedpeople+1):
        for i,rank in enumerate(config["invite-ranks"]):
            if invitedpeoples==rank:
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
    if "manage-role-ids" not in config:
        return []
    roleids=[str(role.id) for role in member.roles]
    managedroleids=sum([config["manage-role-ids"][roleid] for roleid in config["manage-role-ids"] if roleid in roleids],[])
    return sorted(set(managedroleids),key=lambda x:member.guild.get_role(x).name)

def timedeltatostr(td):
    if td.days<1:
        if td.seconds<3600:
            if td.seconds<60:
                return f'{td.seconds} seconds'
            return f'{td.seconds//60} minutes {td.seconds%60} seconds'
    return f'{td.days*24+td.seconds//3600} hours'

def download(url,file_name):
    get_response = requests.get(url,stream=True)
    with open(file_name, 'wb') as f:
        for chunk in get_response.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

def command(client,*,allowedchannels=None,aliases=None,args=None):
    def add_command(func):
        client.commands[func.__name__]=func
        if allowedchannels is not None: # if this command is limited to certain channels
            client.commandlimits[func.__name__]=allowedchannels
        if aliases is not None:
            for alias in aliases:
                client.aliases[alias]=func.__name__
        if args is not None:
            client.commandargs[func.__name__]=args
    return add_command

def split(filename):
    pass
    return
    size=os.path.getsize(filename)
    bsize=1000
    psize=0
    partsize=f
    with open(filename,'rb') as file:
        pass

def lock():
    global lockfile
    try:
        lockfile=open('.lock','r')
        sys.exit()
    except:
        lockfile=open('.lock','w')

def unlock():
    lockfile.close()
    os.remove('.lock')

logfilename=os.path.join('output',f'potato-log-{datetime.datetime.now()}.txt'.replace(':','.'))
logfile=open(logfilename,'w')

logf(logfile,'Starting...')

intents = discord.Intents.all()

with open("token","r") as tokenfile:
    token = tokenfile.read()
logf(logfile,'Read token')

invitersdict=read_inviters()
logf(logfile,'Read inviters')

with open("config.json","r") as configfile:
    allconfig = json.load(configfile)
logf(logfile,'Read config')

client = MyClient(intents=intents)

usecommands=True
if usecommands:
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

    @command(client,args=[['command...',None,'The names of commands to get help about',True]])
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
        if len(message.mentions)==0:
            invites=len(await message.guild.invites())
            members=len(message.guild.members)
            statsmessage=f'Number of invites: {invites}\nNumber of members: {members}'
        elif len(message.mentions)==1:
            statsmessage=(
                'Highest role: `'+max(message.mentions[0].roles).name+'`'+
                '\nTime in server: '+timedeltatostr(datetime.datetime.now()-message.mentions[0].joined_at)+
                '\nNumber of invites: '+str(len([invite for invite in await message.guild.invites() if invite.inviter==message.mentions[0]]))+
                '\nNumber of people invited: '+str(len(invitersdict[message.guild.id][message.mentions[0].id]))
            )
        else:
            statsmessage=''
            for mention in message.mentions:
                statsmessage+=(
                    member_str(mention)+
                    '\nHighest role: `'+max(mention.roles).name+'`'+
                    '\nTime in server: '+timedeltatostr(datetime.datetime.now()-mention.joined_at)+
                    '\nNumber of invites: '+str(len([invite for invite in await message.guild.invites() if invite.inviter==mention]))+
                    '\nNumber of people invited: '+str(len(invitersdict[message.guild.id][message.author.id]))+
                    '\n\n'
                )
        await message.channel.send(statsmessage)

    @command(client)
    async def help_roles(self,message,channel,commandline,config):
        "Show the roles that can be toggled and/or managed"
        if "role-add-any" not in config:
            selftoggleroles='\n'.join(['> `@'+channel.guild.get_role(role).name+'`' for role in config["role-add-any"]])
        else:
            selftoggleroles=''
        managedroleids=get_managed_role_ids(message.author)
        managedroles='\n'.join(['> `@'+channel.guild.get_role(role).name+'`'
            for role in
            managedroleids
        ])
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
        memberids=[int(mid) for mid in commandline[2:]]
        inviters=invitersdict[message.guild.id]
        for memberid in memberids:
            if memberid not in inviters:
                inviters[memberid]=[]
            else:
                try:
                    await update_invite_roles(self,inviters,message.guild.get_member(memberid),config)
                except:
                    pass
            if memberid not in inviters[inviterid]:
                inviters[inviterid].append(memberid)
            try:
                await update_invite_roles(self,inviters,message.guild.get_member(inviterid),config)
            except:
                pass
        write_inviters(inviters)

    @command(client,allowedchannels=modonly,args=[['inviter','id','The ID of the inviter'],['invited','id','The ID of the invited member']])
    async def uninvited(self,message,channel,commandline,config):
        "DO NOT USE!\nManually remove someone from the invited list by ID"
        inviterid=int(commandline[1])
        memberid=int(commandline[2])
        memberids=[int(mid) for mid in commandline[2:]]
        for memberid in memberids:
            inviters=invitersdict[message.guild.id]
            if memberid in inviters[inviterid]:
                inviters[inviterid].remove(memberid)
            await update_invite_roles(self,inviters,message.guild.get_member(inviterid),config)
        write_inviters(inviters)

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
            successmessage='The `@'+message.role_mentions[0].name+'` role has successfully been given to '+member_str(message.mentions[0])+((' '+reason) if reason else '')
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
            successmessage='The `@'+message.role_mentions[0].name+'` role has successfully been removed from '+member_str(message.mentions[0])+((' '+reason) if reason else '')
            await channel.send(successmessage)
            return
        failmessage='You do not have permission to remove `@'+message.role_mentions[0].name+'` from '+member_str(message.mentions[0])
        await channel.send(failmessage)

    @command(client,args=[['role','@role','The role to toggle']])
    async def togglerole(self,message,channel,commandline,config):
        "Toggle a role"
        roles=message.author.roles
        if 'role-add-any' in config and message.role_mentions[0].id in config["role-add-any"]:
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
        if channel.id not in config.get('punishment-channels',[]):
            return
        userstr = commandline[1]
        reason = " ".join(commandline[2:])
        if reason.split()==[]:
            reason="for no reason"

        user=message.mentions[0]
        await channel.guild.kick(user,reason=reason)
        kickmessage="Kicked "+userstr+"\nReason: "+reason
        await channel.send(kickmessage)

        for channelid in config.get("punishment-notification-channels",[]):
            punishment_channel = channel.guild.get_channel(channelid)
            await punishment_channel.send(kickmessage)

    @command(client,allowedchannels=modonly,args=[['person','@person','The person to ban']])
    async def ban(self,message,channel,commandline,config):
        "Ban someone from the server"
        if channel.id not in config.get('punishment-channels',[]):
            return
        userstr = commandline[1]
        reason = " ".join(commandline[2:])
        if reason.split()==[]:
            reason="for no reason"

        user=message.mentions[0]
        await channel.guild.ban(user,reason=reason)

        banmessage="Banned "+userstr+"\nReason: "+reason
        await channel.send(banmessage)

        for channelid in config.get("punishment-notification-channels",[]):
            punishment_channel = channel.guild.get_channel(channelid)
            await punishment_channel.send(banmessage)

    @command(client,allowedchannels=modonly)
    async def reconfig(self,message,channel,commandline,config):
        "Reload the config file"
        global allconfig
        with open("config.json","r") as configfile:
            allconfig = json.load(configfile)
        await message.channel.send('Config successfully reloaded!')

    @command(client,allowedchannels=modonly)
    async def get_attachments(self,message,cchannel,commandline,config):
        channel=cchannel
        folder=f'{datetime.datetime.now()}'.replace(':','.')
        os.mkdir(os.path.join('attachments',f'{folder}'))
        os.mkdir(os.path.join('attachments',f'{folder}','attachments'))
        if len(message.channel_mentions)>0:
            channel=message.channel_mentions[0]
        attachments=[]
        print(channel)
        async for message in channel.history(limit=None,oldest_first=True):
            if len(message.attachments)==0:
                continue
            if message.author==self.user:
                continue
            for attachment in message.attachments:
                print(attachment.filename)
                attachments.append(attachment)
        itr=tqdm.tqdm(attachments)
        for attachment in itr:
            filename=attachment.filename.split('.',maxsplit=1)
            filename[0]+=f'-{message.created_at}.'
            filename=''.join(filename)
            print('\r'+' '*os.get_terminal_size().columns+'\r',end='')
            print('\nDownloading '+attachment.url)
            itr.refresh()
            download(attachment.url, os.path.join('attachments',f'{folder}','attachments',f'{filename}'))
            print('\r'+' '*os.get_terminal_size().columns+'\r',end='')
            print('Finished downloading '+attachment.url)
            itr.refresh()
        print("Finished downloading all files")
        subprocess.run(['./zip',os.path.join('attachments',f'{folder}')])
        print("Finished zipping all files")
        files=[f'attachments.tar.bz2']
        size=os.path.getsize(f'attachments/{folder}/attachments.tar.bz2')
        if size>8000:
            print("File too large, splitting")
            subprocess.run(['./split',f'attachments/{folder}'])
            print("Finished splitting file")
            files=os.listdir(f'attachments/{folder}')
            files.remove('attachments')
            files.remove('attachments.tar.bz2')
            pass
        tmessage=await cchannel.send(f'Attachments in <#{channel}>')
        #thread=await tmessage.create_thread(f'Attachments in {message.channel_mentions[0].name}')
        for file in files:
            with open(f'attachments/{folder}/{file}','rb') as f:
                await cchannel.send(file=discord.File(f))
        shutil.rmtree(f'attachments/{folder}')

    @command(client)
    async def inviters_tree(self,message,channel,commandline,config):
        roots={inviter:{invitee:None for invitee in invitersdict[message.guild.id][inviter]} for inviter in invitersdict[message.guild.id]}
        roots2=roots.copy()
        print(roots)
        for inviter in roots:
            for invitee in roots[inviter]:
                roots[inviter][invitee]=roots[invitee]
                try:
                    if inviter!=invitee:
                        del roots2[invitee]
                except:
                    pass
        def formatd(d,g,ids=None):
            if ids is None:
                ids=[]
            if id(d) in ids:
                return ''
            if len(d)==0:
                return ''
            out=''
            for i in d:
                f=formatd(d[i],g,ids+[id(d)])
                if f=='':
                    out+='\n'+member_id_str(i,g)
                    continue
                out+='\n'+member_id_str(i,g)+f.replace('\n','\n\t')
            return out
        print(formatd(roots2,message.guild))
        await send_big_message(formatd(roots2,message.guild),channel)

    @command(client,allowedchannels=modonly)
    async def code(self,message,channel,commandline,config):
        with open(sys.argv[0],'rb') as f:
            await channel.send(file=discord.File(f))

    @command(client,allowedchannels=modonly)
    async def restart(self,message,channel,commandline,config):
        unlock()
        sys.exit()

logf(logfile,"Initialized client")
client.run(token)
