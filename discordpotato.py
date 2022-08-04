import discord


class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        # don't respond to ourselves
        print(message.content)
        if message.author == self.user:
            return
        if self.has_potato(message):
            await message.add_reaction('🥔')
        if message.content.lower().startswith('!ping'):
            await message.channel.send("Pong!")
        if message.channel.name=='punishments' and message.content.lower().startswith('!kick '):
            userstr = message.content.lower().split()[1]
            reason = " ".join(message.content.lower().split()[2:])
            if reason.split()==[]:
                reason="for no reason"
            print(message.mentions[0])
            user=message.mentions[0]
            await message.channel.guild.kick(user,reason=reason)
            await message.channel.send("Kicked "+userstr+"\nReason: "+reason)
            punishment_channel = message.channel.guild.get_channel(1000561797557932134)
            await punishment_channel.send("Kicked "+userstr+"\nReason: "+reason)

    async def on_message_edit(self, m_before, m_after):
        this_user = m_after.channel.guild.get_member(self.user.id)
        print(m_before.content, m_after.content)
        if self.has_potato(m_after):
            await m_after.add_reaction('🥔')
        if not self.has_potato(m_after):
            await m_after.remove_reaction('🥔',this_user)

    async def on_member_update(self, m_before, m_after):
        pass

    async def on_member_join(self, member):
        print("a member joined!")
        welcome_channel=member.guild.get_channel(1000561459266326588)
        print(member,welcome_channel)
        await welcome_channel.send("@everyone welcome the newest member of this server <@"+member.id+">!")
        #await member.add_roles(,reason="on join")

    def has_potato(self,message):
        return 'potat' in message.content.lower() or '🥔' in message.content.lower()

intents = discord.Intents.all()
with open("token","r") as tokenfile:
    token = tokenfile.read()
client = MyClient()
with open("token","r") as tokenfile:
    token = tokenfile.read()
client.run(token)
