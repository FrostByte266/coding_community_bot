"""
Commands provided by this cog.

	networkplot : Prots connections between user roles on the server
	plot : Gives a graph of role usage in the server
	uptime: Shows the bot uptime
"""

from datetime import datetime
from discord.ext import commands
from discord import File
from pandas import DataFrame
from utils import metrics_utils
import matplotlib.pyplot as plt
import networkx as nx
import itertools


class Metrics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def networkplot(self, ctx):
        # Create dict of role names and the number of members in each
        default_role = '@everyone'
        roles = [str(role.name) for role in ctx.guild.roles if role.name != default_role]
        
        df = DataFrame(columns=roles, index=roles)
        df[:] = int(0)

        for member in ctx.guild.members:
            member_roles = [role.name for role in member.roles if role.name != default_role]
            for role, co_role in itertools.product(member_roles, repeat=2):
                df.loc[role, co_role] += 1
                df.loc[co_role, role] += 1

            max_connection_weight = df.max().max()

        edge_list = []
        for index, row in df.iterrows():
            i = 0
            for col in row:
                weight = float(col) / max_connection_weight
                edge_list.append((index, df.columns[i], weight))
                i += 1

        # Remove edge if 0.0
        updated_edge_list = [x for x in edge_list if not x[2] == 0.0]

        node_list = []
        for role, edge in itertools.product(roles, updated_edge_list):
            if all((role == edge[0], role == edge[1])):
                node_list.append((role, edge[2] * 6))
        
        [node_list.remove(i) for i in node_list if i[1] == 0.0]

        # remove self references
        [updated_edge_list.remove(i) for i in updated_edge_list if i[0] == i[1]]

        # Create plot

        # set canvas size
        plt.subplots(figsize=(14, 14))

        # networkx graph time!
        graph = nx.Graph()
        [graph.add_node(i[0], size=i[1]) for i in sorted(node_list)]
        graph.add_weighted_edges_from(updated_edge_list)

        # check data of graphs
        # G.nodes(data=True)
        # G.edges(data = True)

        # manually copy and pasted the node order using 'nx.nodes(G)'
        # Couldn't determine another route to listing out the order of nodes
        # for future work
        node_order = [str(x) for x in nx.nodes(graph)]

        # reorder node list
        updated_node_order = []
        for i, x in itertools.product(node_order, node_list):
            if x[0] == i:
                updated_node_order.append(x)


        # reorder edge list
        test = nx.get_edge_attributes(graph, 'weight')
        updated_again_edges = []
        for i, x in itertools.product(nx.edges(graph), test.keys()):
            if all((i[0] == x[0], i[1] == x[1])):
                updated_again_edges.append(test[x])

        # Drawing customization
        node_scalar = 1600
        edge_scalar = 20
        sizes = [x[1] * node_scalar for x in updated_node_order]
        widths = [x * edge_scalar for x in updated_again_edges]

        # Draw the graph
        pos = nx.spring_layout(graph, k=0.42, iterations=17)
        plt.title(f'{ctx.guild.name} role co-occurrence graph')
        nx.draw(
            graph, pos,
            with_labels=True,
            font_size=8,
            font_weight='bold',
            node_size=sizes,
            width=widths
        )

        # One co-occurrence image per server
        image_path = f'./assets/network_charts/{ctx.guild.id}.png'
        plt.savefig(image_path, format="PNG")
        await ctx.message.author.send(f'{ctx.guild.name} roles chart', file=File(image_path))

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def plot(self, ctx):
        # Create dict of role names and the number of members in each
        roles_dict = {role.name: [len(role.members)]
                      for role in ctx.guild.roles}
        roles_dict.pop('@everyone', None)

        # Create plot
        data_frame = DataFrame.from_dict(roles_dict).sort_values(
            by=0, axis=1, ascending=False).transpose()
        sizing = len(data_frame.columns) * 2
        data_frame.plot(
            title=f"{ctx.guild.name} roles on {datetime.today().strftime('%Y-%m-%d')}\n"
            f"Average: {data_frame.describe().iloc[1].head(1)[0]} "
            f" Std. Dev: {round(data_frame.describe().iloc[2].head(1)[0],4)}\n"
            f"Higher Quartile: {data_frame.describe().iloc[6].head(1)[0]} "
            f" Lower Quartile: {data_frame.describe().iloc[4].head(1)[0]}",
            kind='bar',
            width=.2, rot=90,
            fontsize=12,
            legend=False,
            figsize=(20 + sizing * 2, 10 + sizing)
        )

        # One roles images per server
        image_path = f'./assets/role_charts/{ctx.guild.id}.png'
        plt.draw()
        plt.tight_layout()
        plt.savefig(image_path)
        await ctx.message.author.send(f'{ctx.guild.name} roles chart', file=File(image_path))

    @commands.command(description="Show uptime")
    @commands.has_permissions(manage_messages=True)
    async def uptime(self, ctx):
        """
        View bot uptime.

        usage:
                !uptime
        """

        await ctx.send(await metrics_utils.uptime_calculation(self.bot))


def setup(bot):
    try:
        bot.add_cog(Metrics(bot))
    except Exception as squawk:
        print(squawk)
