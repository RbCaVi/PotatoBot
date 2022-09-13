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

invites = {}

inviters={}

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user) 
        # Getting all the guilds our bot is in
        for guild in self.guilds:
            # Adding each guild's invites to our dict
            invites[guild.id] = await guild.invites()

    async def on_message(self, message):
        # don't respond to ourselves
        print(message.content)
        if message.author == self.user:
            return
        channel=message.channel
        if self.has_potato(message):
            await message.add_reaction('🥔')
        if self.is_forbidden(message):
            await message.delete()
        if message.content.lower().startswith('!ping'):
            await channel.send("Pong!")
        if message.content.lower().startswith('!help'):
            await channel.send(helpmessage)
        if message.content.lower().startswith('!users'):
            users=message.guild.members
            await channel.send('\n'.join(["<@"+str(mem.id)+">" for mem in sorted(message.guild.members,key=lambda x:x.nick or x.name)]))
        if message.content.lower().startswith('!invited'):
            inviterid=int(message.content.lower().split()[1])
            memberid=int(message.content.lower().split()[2])
            if memberid not in inviters:
                inviters[memberid]=[]
            if memberid not in inviters[inviterid]:
                inviters[inviterid].append(memberid)
            write_inviters(inviters)
        if message.content.lower().startswith('!inviters'):
            #print(inviters)
            guild=channel.guild
            print('\n'.join(sorted([
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
            await channel.send('\n'.join(sorted([
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
        if message.content.lower().startswith('!invites'):
            invites=await message.guild.invites()
            invites=[member_str(invite.inviter)+": https://discord.gg/"+invite.code for invite in invites]
            await channel.send('\n'.join(invites))
        if channel.name=='punishments':
            if message.content.lower().startswith('!kick '):
                userstr = message.content.lower().split()[1]
                reason = " ".join(message.content.lower().split()[2:])
                if reason.split()==[]:
                    reason="for no reason"
                print(message.mentions[0])
                user=message.mentions[0]
                await channel.guild.kick(user,reason=reason)
                await channel.send("Kicked "+userstr+"\nReason: "+reason)
                punishment_channel = channel.guild.get_channel(1000561797557932134)
                await punishment_channel.send("Kicked "+userstr+"\nReason: "+reason)
            if message.content.lower().startswith('!ban '):
                userstr = message.content.lower().split()[1]
                reason = " ".join(message.content.lower().split()[2:])
                if reason.split()==[]:
                    reason="for no reason"
                print(message.mentions[0])
                user=message.mentions[0]
                await channel.guild.ban(user,reason=reason)
                banmessage="Banned "+userstr+"\nReason: "+reason
                await channel.send(banmessage)
                punishment_channel = channel.guild.get_channel(1000561797557932134)
                await punishment_channel.send(banmessage)

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

        # Getting the invites before the user joining
        # from our cache for this specific guild

        invites_before_join = invites[member.guild.id]

        # Getting the invites after the user joining
        # so we can compare it with the first one, and
        # see which invite uses number increased

        invites_after_join = await member.guild.invites()

        # Loops for each invite we have for the guild
        # the user joined.

        for invite in invites_before_join:

            # Now, we're using the function we created just
            # before to check which invite count is bigger
            # than it was before the user joined.
            
            if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses:
                
                # Now that we found which link was used,
                # we will print a couple things in our console:
                # the name, invite code used the the person
                # who created the invite code, or the inviter.
                
                print(f"Member {member_str(member)} Joined")
                print(f"Invite Code: {invite.code}")
                print(f"Inviter: {invite.inviter}")
                print(f"Member {member.id} Joined")
                print(f"Inviter: {invite.inviter.id}")
                
                if member.id not in inviters:
                    inviters[member.id]=[]
                if member.id not in inviters[invite.inviter.id]:
                    inviters[invite.inviter.id].append(member.id)
                write_inviters(inviters)

                # We will now update our cache so it's ready
                # for the next user that joins the guild

                invites[member.guild.id] = invites_after_join
                
                # We return here since we already found which 
                # one was used and there is no point in
                # looping when we already got what we wanted
                return

    def has_potato(self,message):
        processed_message=process(message.content)
        return 'potat' in processed_message or '🥔' in processed_message

    def is_forbidden(self,message):
        processed_message=process(message.content)
        for forbidden in ['\x63\x61\x72\x72\x6f\x74','\x63\x61\x72\x6f\x74','\x63\x61\x72\x72\x61\x74','\x63\x61\x72\x61\x74','\xf0\x9f\xa5\x95']:
            if forbidden in processed_message:
                return True
        return False

    async def on_member_remove(self,member):
    
        # Updates the cache when a user leaves to make sure
        # everything is up to date
        
        invites[member.guild.id] = await member.guild.invites()

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
    
    # Simply looping through each invite in an
    # invite list which we will get using guild.invites()
    
    for inv in invite_list:
        
        # Check if the invite code in this element
        # of the list is the one we're looking for
        
        if inv.code == code:
            
            # If it is, we return it.
            
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

print('Starting...')

intents = discord.Intents.all()

with open("token","r") as tokenfile:
    token = tokenfile.read()

inviters=read_inviters()

intents = discord.Intents.all()
client = MyClient(intents=intents)

print("Initialized client")

with open("config.json","r") as configfile:
    config = json.loads(configfile.read())

print('Read token')
client.run(token)
