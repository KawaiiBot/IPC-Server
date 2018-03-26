from discord.ext import commands
from utils import repo


class IPC:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def instance(self, ctx):
        """ Displays the current instance ID """
        await ctx.send(self.bot.instance)

    @commands.command(name="global")
    @commands.is_owner()
    async def global_(self, ctx, command: str, *, args: str):
        """ Executes the specified command across the other instances

        Command  |  Arguments  |  Returns
        eval        *             *
        reload      cog           bool
        """
        data = {
            'op': 'EXEC',
            'id': self.bot.instance,
            'd': {
                'command': command,
                'args': args
            }
        }
        res = await self.bot.conn.send(data, expect_result=True)
        await ctx.send(f"```py\n{str(res)}\n```")


def setup(bot):
    bot.add_cog(IPC(bot))
