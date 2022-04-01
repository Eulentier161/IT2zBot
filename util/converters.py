import re


class Converter:
    @staticmethod
    async def convert_member(ctx, member):

        # lookup by ID/mention
        string_for_mention = re.sub("<|!|@|>", "", member)
        try:
            item = ctx.guild.get_member(int(string_for_mention))
            return item
        except:
            pass

        # lookup by name#discrim
        for item in ctx.guild.members:
            if f"{item.name.lower()}#{item.discriminator}" == member.lower():
                return item

        # lookup by name
        for item in ctx.guild.members:
            if item.name.lower() == member.lower():
                return item

        # lookup by nickname
        for item in ctx.guild.members:
            if item.nick != None:
                if item.nick.lower() == member.lower():
                    return item

    @staticmethod
    async def convert_role(ctx, role):

        # lookup by ID/mention
        string_for_mention = re.sub("<|&|@|>", "", role)
        try:
            item = ctx.guild.get_role(int(string_for_mention))
            return item
        except:
            pass

        for item in ctx.guild.roles:
            # lookup by name
            if item.name.lower() == role.lower():
                return item

    @staticmethod
    async def convert_textchannel(ctx, channel):

        string_mor_mention = re.sub("<|#|>", "", channel)
        try:
            item = ctx.guild.get_channel(int(string_mor_mention))
            return item
        except:
            pass

        for item in ctx.guild.channels:
            if item.name.lower() == channel.lower():
                return item
