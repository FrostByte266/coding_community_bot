"""
Commands provided by this cog.

    kick : Kicks a user. A message is sent to the kicking user and kicked.
    ban  : Bans a user. A message is sent to the banning user and the banned.
    hackban : Bans someone who is not in the guild.
    unban : Unbans a user. A message is sent the the issuer and the recipient.
    report : Reports a user. A message is sent to the issuer and the recipient.
    lookup : Looks up a report by user or incident id.
    recall : Clears a single report. Requires an incident id.
"""

from datetime import datetime, timedelta, timezone
import json

from discord import Embed, Guild, User
from discord.utils import get
from discord.errors import Forbidden
from discord.ext import commands, tasks


class IncidentReport:

    def __init__(self, server: Guild, action: str, body: str, issuer: User, subject: User):
        self.action = action
        self.issuer = issuer
        self.subject = subject
        self.body = body
        self.server = server
        self.config_path = 'assets/config.json'
        self.config_full = json.loads(open(self.config_path).read())
        self.config = self.config_full[str(self.server.id)]
        self.report_number = self.next_report_number()
        self.finalize_report()

    def next_report_number(self):
        return len(self.config['reports']) + 1

    def finalize_report(self):
        report = {
            "report_id": self.report_number,
            "action": self.action,
            "issuer": f'{self.issuer.name}#{self.issuer.discriminator}',
            "subject": f'{self.subject.name}#{self.subject.discriminator}',
            "body": self.body
        }
        self.config["reports"].update({self.report_number: report})
        json.dump(self.config_full, open(self.config_path, 'w'),
                  indent=2, separators=(',', ': '))

    def generate_receipt(self):
        embed = Embed(title='Incident Report',
                      description=f'Case Number: {self.report_number}', color=0xff0000)
        embed.add_field(name="Issued By:",
                        value=f'{self.issuer.name}#{self.issuer.discriminator}')
        embed.add_field(
            name="Subject:", value=f'{self.subject.name}#{self.subject.discriminator}')
        embed.add_field(name='Action', value=self.action)
        embed.add_field(name='Reason', value=self.body)
        embed.timestamp = datetime.utcnow()
        return embed


async def handle_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            'You have not entered all required parameters, use b!help <command> for a list of all parameters')
    elif isinstance(error, commands.BadArgument):
        await ctx.send("User not found! Double check you entered the correct details!")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send('You are missing the required permissions')

async def tempban_core(guild, target, time_to_expire, reason):

    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=time_to_expire)
    unix_timestamp = int(expiration_time.timestamp())

    if len(reason) > 510:
        reason = f'Ban reason exceeded 512 characters.'

    await guild.ban(target, reason=f'tempban {unix_timestamp} | {reason}')

class Punishment(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config_path = 'assets/config.json'
        self.config_full = json.loads(open(self.config_path).read())
        self.tempban_expiration_task.start()

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, target: User, *, reason: str):
        """Kick the specified user (a report receipt will be send to the recipient and issuer,
        and optionally reporting channel if enabled)"""
        report = IncidentReport(ctx.message.guild, 'Kick',
                                reason, ctx.message.author, target)
        receipt = report.generate_receipt()
        await ctx.message.author.send(
            f'User: {target.name}#{target.discriminator} has been kicked. The incident report is attached below:',
            embed=receipt)
        await target.send(
            f'You have been kicked from {ctx.message.guild}. The incident report is attached below:',
            embed=receipt
        )
        await ctx.message.guild.kick(target, reason=reason)
        await ctx.send(f'User: {target.name}#{target.discriminator} has been kicked. Report ID: {report.report_number}')
        reporting_enabled = True if self.config_full[str(ctx.message.guild.id)][
            "reporting_channel"] is not None else False
        if reporting_enabled:
            report_channel = get(
                ctx.message.guild.text_channels,
                id=self.config_full[str(
                    ctx.message.guild.id)]["reporting_channel"]
            )
            await report_channel.send(embed=receipt)

    @kick.error
    async def kick_error(self, ctx, error):
        await handle_error(ctx, error)

    def check_expired(self, entry):
        has_tempban_flag = entry.reason.startswith('tempban')

        expiration_date = datetime.fromtimestamp(int(entry.reason.split()[1]), timezone.utc)
        entry_is_expired = datetime.now(timezone.utc) > expiration_date

        return has_tempban_flag and entry_is_expired  

    @tasks.loop(hours=1)
    async def tempban_expiration_task(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            expired_entries = filter(self.check_expired, await guild.bans())
            users_to_unban = (entry.user for entry in expired_entries)
            for user in users_to_unban:
                await guild.unban(user, reason='Temporary ban expired')

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def tempban(self, ctx, target: User, *, reason: str):
        report = IncidentReport(ctx.guild, 'Temporary Ban',
                                reason, ctx.author, target)
        receipt = report.generate_receipt()
        try:
            await target.send(f'You have been temporarily banned from {ctx.guild} to '
                            f'give the administration team an opportunity to further evaluate' 
                            f'the matter. At the conclusion of their evaluation, you may '
                            f'be permanently banned.', embed=receipt)
            warning_dm_sent = True
        except Forbidden:
            warning_dm_sent = False

        receipt.add_field(name='Target received warning DM', value=warning_dm_sent)
        try:
            await ctx.author.send(f'User: {target} has ben temporarily banned. Please '
                                f'follow up with the administration team', embed=receipt)
        except Forbidden:
            pass

        if len(reason) > 510:
            reason = f'Ban reason exceeded 512 characters. Please review report #{report.report_number}'

        await tempban_core(ctx.guild, reason, 86400)
        await ctx.send(f'User {target} was temporarily banned. Report ID: {report.report_number}')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, target: User, *, reason: str):
        """Ban the specified user (a report receipt will be sent to the recipient and issuer,
        and optionally reporting channel if enabled)"""
        report = IncidentReport(ctx.message.guild, 'Ban',
                                reason, ctx.message.author, target)
        receipt = report.generate_receipt()
        await ctx.message.author.send(
            f'User: {target.name}#{target.discriminator} has been banned. The incident report is attached below:',
            embed=receipt)
        await target.send(
            f'You have been banned from {ctx.message.guild}. The incident report is attached below:',
            embed=receipt
        )
        if len(reason)>510:
            reason = f'Ban reason exceeded 512 characters. Please review report #{report.report_number}'
        await ctx.message.guild.ban(target, reason=reason, delete_message_days=0)
        await ctx.send(f'User: {target.name}#{target.discriminator} has been banned. Report ID: {report.report_number}')
        reporting_enabled = True if self.config_full[str(ctx.message.guild.id)][
            "reporting_channel"] is not None else False
        if reporting_enabled:
            report_channel = get(
                ctx.message.guild.text_channels,
                id=self.config_full[str(
                    ctx.message.guild.id)]["reporting_channel"]
            )
            await report_channel.send(embed=receipt)

    @ban.error
    async def ban_error(self, ctx, error):
        await handle_error(ctx, error)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def hackban(self, ctx, target: int, *, reason: str):
        """Ban a user not in the server"""
        user = await self.bot.fetch_user(target)
        tempban = find(lambda entry: entry.user == user and entry.reason.startswith('tempban'), await ctx.guild.bans())
        if tempban is not None:
            # Get the original reason without the tempban marker
            original_reason = tempban.reason[tempban.reason.find('|'):].strip()
            await ctx.guild.unban(user, reason='Temporary reversal')
            reason = f'Tempban verified and converted to permaban. Additional comment: {reason}\nOriginal reason: {original_reason}'

        report = IncidentReport(
            ctx.message.guild, 'Hackban', reason, ctx.message.author, user)
        receipt = report.generate_receipt()

        try:
            await ctx.message.author.send(
                f'User: {user.name}#{user.discriminator} has been hackbanned. The incident report is attached below:',
                embed=receipt)
        except Forbidden:
            pass

        if len(reason)>510:
            reason = f'Ban reason exceeded 512 characters. Please review report #{report.report_number}'
        await ctx.guild.ban(user, reason=reason, delete_message_days=0)
        await ctx.send(f'User: {user.name}#{user.discriminator} has been hackbanned. Report ID: {report.report_number}')

        reporting_enabled = True if self.config_full[str(ctx.message.guild.id)][
            "reporting_channel"] is not None else False

        if reporting_enabled:
            report_channel = get(
                ctx.message.guild.text_channels,
                id=self.config_full[str(
                    ctx.message.guild.id)]["reporting_channel"]
            )
            await report_channel.send(embed=receipt)

    @hackban.error
    async def hackban_error(self, ctx, error):
        await handle_error(ctx, error)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, target_id: int, *, reason: str):
        """Unban the specified user (a report receipt will be sent to the recipient and
        issuer, and optionally reporting channel if enabled, user ID number required)"""
        target = await self.bot.fetch_user(target_id)
        report = IncidentReport(
            ctx.message.guild, 'Unban', reason, ctx.message.author, target)
        receipt = report.generate_receipt()
        await ctx.message.author.send(
            f'User: {target.name}#{target.discriminator} has been unbanned. The incident report is attached below:',
            embed=receipt)
        await ctx.message.guild.unban(target)
        await ctx.send(
            f'User: {target.name}#{target.discriminator} has been unbanned. Report ID: {report.report_number}')
        reporting_enabled = True if self.config_full[str(ctx.message.guild.id)][
            "reporting_channel"] is not None else False
        if reporting_enabled:
            report_channel = get(
                ctx.message.guild.text_channels,
                id=self.config_full[str(
                    ctx.message.guild.id)]["reporting_channel"]
            )
            await report_channel.send(embed=receipt)

    @unban.error
    async def unban_error(self, ctx, error):
        await handle_error(ctx, error)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def report(self, ctx, target: User, action: str, *, reason: str):
        """Create a custom incident report, action must be one word
        (receipt will be sent to recipient and issuer, and optionally reporting channel if enabled) """
        report = IncidentReport(ctx.message.guild, action,
                                reason, ctx.message.author, target)
        receipt = report.generate_receipt()
        await ctx.message.author.send(f'Incident report receipt:', embed=receipt)
        await target.send(f'Incident report receipt:', embed=receipt)
        reporting_enabled = True if self.config_full[str(ctx.message.guild.id)][
            "reporting_channel"] is not None else False
        if reporting_enabled:
            report_channel = get(
                ctx.message.guild.text_channels,
                id=self.config_full[str(
                    ctx.message.guild.id)]["reporting_channel"]
            )
            await report_channel.send(embed=receipt)

    @report.error
    async def report_error(self, ctx, error):
        await handle_error(ctx, error)

    @commands.command()
    async def lookup(self, ctx, *, args: str):
        """Search for a report by user ID, mention, or report ID number, use b!lookup <report id> --receipt
        to have a copy sent to you via DM"""
        config = self.config_full[str(ctx.message.guild.id)]
        reports = config["reports"]
        length_args = len(args.strip())
        embed = None
        if length_args == 18:
            # User ID has been provided
            user = await self.bot.fetch_user(args)
            user_name = f'{user.name}#{user.discriminator}'

            reports = config["reports"]
            results = [str(report) for report in config["reports"]
                       if any((
                                reports[str(report)]["issuer"] == user_name,
                                reports[str(report)]["subject"] == user_name
                                ))
                       ]

            if results:
                for result in results:
                    embed = Embed(
                        title='Incident Report', description=f'Case Number: {reports[result]["report_id"]}',
                        color=0xff0000
                    )
                    embed.add_field(name="Issued By:",
                                    value=reports[result]["issuer"])
                    embed.add_field(name="Subject:",
                                    value=reports[result]["subject"])
                    embed.add_field(
                        name='Action', value=reports[result]["action"])
                    embed.add_field(
                        name='Reason', value=reports[result]["body"])
                    await ctx.send(embed=embed)
            else:
                await ctx.send('No reports found with the user provided')
        elif ctx.message.mentions:
            # User provided via mention
            user = ctx.message.mentions[0]
            user_name = f'{user.name}#{user.discriminator}'
            reports = config["reports"]
            results = [str(report) for report in config["reports"] if reports[str(report)]["subject"] == user_name]

            if results:
                for result in results:
                    embed = Embed(
                        title='Incident Report', description=f'Case Number: {reports[result]["report_id"]}',
                        color=0xff0000
                    )
                    embed.add_field(name="Issued By:",
                                    value=reports[result]["issuer"])
                    embed.add_field(name="Subject:",
                                    value=reports[result]["subject"])
                    embed.add_field(
                        name='Action', value=reports[result]["action"])
                    embed.add_field(
                        name='Reason', value=reports[result]["body"])
                    await ctx.send(embed=embed)
            else:
                await ctx.send('No reports found with the user provided')
        else:
            # Looking up by ID as no users were mentioned
            report_id = args.split(' ')[0]
            report = reports.get(str(report_id), None)
            if report is not None:
                embed = Embed(
                    title='Incident Report', description=f'Case Number: {report["report_id"]}',
                    color=0xff0000
                )
                embed.add_field(name="Issued By:", value=report["issuer"])
                embed.add_field(name="Subject:", value=report["subject"])
                embed.add_field(name='Action', value=report["action"])
                embed.add_field(name='Reason', value=report["body"])
                await ctx.send(embed=embed)
            else:
                await ctx.send('No reports found with the ID number provided')
        if all((not ctx.message.mentions, args.endswith("--receipt"))):
            # If user requests a copy of the report, DM it to them (only single reports can be sent via DM)
            await ctx.message.author.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def recall(self, ctx, report_id: str):
        """Clear a single report, you must have the ID number. If you need the report number,
        use b!lookup <user mention or ID> to find the number"""
        try:
            config = self.config_full[str(ctx.message.guild.id)]
            reports = config["reports"]
            reports.pop(report_id)
            json.dump(self.config_full, open(self.config_path,
                                             'w'), indent=2, separators=(',', ': '))
            await ctx.send(f'Report #{report_id} successfully cleared!')
        except KeyError:
            await ctx.send('No report with that ID was found, double check the ID you entered')


def setup(bot):
    bot.add_cog(Punishment(bot))
