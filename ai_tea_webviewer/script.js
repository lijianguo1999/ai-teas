var title = "<span id='maintitle'>MAPPING THE BIOECONOMY:</span><br><i>Generating Techno-Economic Analyses with AI</i>";
var author = "<a class='author' href='https://homeworld.bio/'>Homeworld Collective</a>"

let md = window.markdownit({html: true});

var width;
var height;

var spotlightProcess;

var papersJSON, papersJSON;

var hasClickedNode = false;

var compareProcess = 0; // when 0, not comparing, when higher, comparing

$("document").ready(function(){
    width = $(window).width();
    height = $(window).height();
    loadJSON().then(() => {
        displayPapers();
        displayProcess();
        loadViz();
    });
    // search bar functionality - searches the papers for matching text
    $('.search-input').on('input', function() {
        var searchValue = $(this).val().toLowerCase();

        $('#papers .paper-info').each(function() {
            var paperInfo = $(this).text().toLowerCase();
            if (paperInfo.indexOf(searchValue) !== -1) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });
});

$("#handle-vert-1").draggable({
    grid: [50, 50],
    axis: "x",
    containment: "#container",
    zIndex: 100,
    drag: function(event, ui){
        ui.position.left = Math.min(Math.max( 50, ui.position.left ), width - 100);
        let x = ui.position.left + 12.5;

        $("#handle-horiz-1").css("right", (width - x) / 2 - 12.5)

        $("#left").css("width", x);

        if (x < 700) {
            smallerText();
        } else {
            biggerText();
        }

        recenterViz();
    }
});

function smallerText() {
    $(".paper-info").css("width", "100%");
    $("#title").css("font-size", "2.5rem");
    $(".paper-info").css("font-size", ".75rem");
    $(".search-input").css("width", "75%");
}

function biggerText() {
    $(".paper-info").css("width", "calc(50% - 10px)");
    $("#title").css("font-size", "3.5rem");
    $(".paper-info").css("font-size", ".9rem");
    $(".search-input").css("width", "50%");
}

$("#handle-horiz-1").draggable({
    grid: [50, 50],
    axis: "y",
    containment: "#container",
    zIndex: 100,
    drag: function(event, ui){
        ui.position.top = Math.min(Math.max( 50, ui.position.top ), width - 100);
        let y = ui.position.top + 12.5;

        $("#right-top").css("height", y);
        $("#right-bottom").css("height", height - y);

        // loadViz();

    }
});

// add event listener to add spotlight process when fab is pressed
$("#add-process-fab").click(function() {
    if ($("#add-process-fab").html() === "+") {
        addProcess();
        compareProcess++;
    } else {
        removeProcess();
        compareProcess = 0;
    }
});
function addProcess() {
    // adjust size of divs, draggable elements, and text size
    $("#left").css("width", "25%");
    $("#handle-vert-1").css("left", "calc(25vw - 12.5px)");
    $("#handle-horiz-1").css("right", "calc(37.5vw - 12.5px)");
    $("#right").css("width", "75%");
    smallerText();
    // show processes side by side, and scrollable
    $("#right-bottom").css("display", "flex");
    $("#right-bottom-right").css("display", "block");
    $("#right-bottom").css("overflow", "hidden");
    $("#right-bottom-left").css("width", "50%");
    // change button to remove process
    $("#add-process-fab").html("-");
    simulation.force("center", d3.forceCenter(width * 0.75 / 2, $("#viz").height() / 2));
}

function removeProcess() {
    $("#left").css("width", "50%");
    $("#handle-vert-1").css("left", "calc(50vw - 12.5px)");
    $("#handle-horiz-1").css("right", "calc(25vw - 12.5px)");
    $("#right").css("width", "50%");
    biggerText();
    $("#right-bottom").css("display", "block");
    $("#right-bottom-right").css("display", "none");
    $("#right-bottom").css("overflow", "scroll");
    $("#right-bottom-left").css("width", "100%");
    $("#add-process-fab").html("+");
    simulation.force("center", d3.forceCenter(width / 4, $("#viz").height() / 2));
}

function loadJSON(){

    return new Promise((resolve, reject) => {
        $.ajax({
            url: `papers_final.json`,
            datatype: "json",
            success: function(data){
                papersJSON = data;
                // var mamlString = papersJSON[0].maml.replace(/(\s*?{\s*?|\s*?,\s*?)(.*?)\s*?:\s*?/g, '$1"$2":').replace(/:\s*?(.*?)\s*?(,|\s*?}\s*?)/g, ':"$1"$2');
                // console.log("pre-maml:", mamlString);
                // try {
                //     papersJSON[0].maml = JSON.parse(mamlString);
                // } catch (error) {
                //     console.error('Error parsing JSON:', error);
                //     // Print the part of the JSON string around the position where the error occurred
                //     var errorPosition = parseInt(error.message.match(/position (\d+)/)[1]);
                //     console.error('Around error:', mamlString.slice(errorPosition - 20, errorPosition + 20));
                // }
                papersJSON.forEach(function(paper) {
                    // var mamlString = paper.maml.replace(/(\s*?{\s*?|\s*?,\s*?)([^":\s]+)\s*?:\s*?(.*?)(,|\s*?}\s*?)/g, function(_, p1, p2, p3, p4) {
                    //     console.log(p2);
                    //     // if (p2 === "{'type'") {
                    //     //     console.log("TYPE");
                    //     //     console.log(p3);
                    //     // }
                    //     // If the key is "id" or "title", don't add extra quotes
                    //     if (p2 === "'id'" || p2 === "'title'" || p2 === "'parameters'" || p2 === "'output'" || p2 === "'input'" || p2 === "'options'" || p2 === "'process_flow'" || p2 === "'type'") {
                    //         return `${p1}${p2.replace(/'/g, '"')}:${p3}${p4}`;
                    //     } else {
                    //         return `${p1}"${p2}":${p3}${p4}`;
                    //     }
                    // });
                    // mamlString = mamlString.replace(/\\(?![bfnrt"\\/])/g, '\\\\');
                    // mamlString = mamlString.replace(/'/g, '"');
                    // console.log('maml:', mamlString);
                    try {
                        paper.maml = JSON5.parse(paper.maml);
                    } catch (error) {
                        console.error('Error parsing JSON:', error);
                        var match = error.message.match(/at (\d+):(\d+)/);
                        if (match) {
                            var lineNumber = parseInt(match[1]);
                            var columnNumber = parseInt(match[2]);
                            console.error('Error at line:', lineNumber, 'column:', columnNumber);
                    
                            // Split the string into lines and get the line with the error
                            var lines = mamlString.split('\n');
                            if (lines.length >= lineNumber) {
                                var errorLine = lines[lineNumber - 1];
                                // Print the part of the line around the error
                                var start = Math.max(0, columnNumber - 21);
                                var end = Math.min(errorLine.length, columnNumber + 20);
                                console.error('Around error:', errorLine.slice(start, end));
                            }
                        }
                    }
                    // if (mamlString.trim().length === 0 || !mamlString.trim().startsWith('{')) {
                    //     console.error('Invalid JSON:', mamlString);
                    // } else {
                    //     try {
                    //         paper.maml = JSON5.parse(paper.maml);
                    //     } catch (error) {
                    //         console.error('Error parsing JSON:', error);
                    //         var match = error.message.match(/at (\d+):(\d+)/);
                    //         if (match) {
                    //             var lineNumber = parseInt(match[1]);
                    //             var columnNumber = parseInt(match[2]);
                    //             console.error('Error at line:', lineNumber, 'column:', columnNumber);
                        
                    //             // Split the string into lines and get the line with the error
                    //             var lines = mamlString.split('\n');
                    //             if (lines.length >= lineNumber) {
                    //                 var errorLine = lines[lineNumber - 1];
                    //                 // Print the part of the line around the error
                    //                 var start = Math.max(0, columnNumber - 21);
                    //                 var end = Math.min(errorLine.length, columnNumber + 20);
                    //                 console.error('Around error:', errorLine.slice(start, end));
                    //             }
                    //         }
                    //     }
                    // }
                });
                resolve();
            },
            error: function(error){
                reject(error);
            }
        });
    });    
}

// function loadPapers(){

//     return new Promise((resolve, reject) => {
//         $.ajax({
//             url: `papers_spreadsheet_2.json`,
//             datatype: "json",
//             success: function(data){
//                 papersJSON = data;
//                 resolve();
//             },
//             error: function(error){
//                 reject(error);
//             }
//         });
//     });    
// }


//convert papers.json into markdown, to display the papers
function displayPapers(){
    $("#title").html(title + "<br>by " + author);
    let paper_md = ``;
    // Iterate over each object in the JSON data
    papersJSON.forEach((item, index) => {
        if (item.maml) {
            // encapsulate in larger class for styling
            paper_md += `<div class="paper-info width-50">\n\n`;
            // Add a header with the title
            paper_md += `## ${item.maml.title}\n\n`;

            // display the input and output tags
            paper_md += `<div class="process-tags in-out-tags"><img class="process-step-img" src="img/feedstock.png">`;
            feedstock_tags = convertToArray(item.feedstock_tags);
            feedstock_tags.forEach((tag, index) => {
                paper_md += `<div class="paper-tag">${removeUnderscores(tag)}</div>`;
            });
            paper_md += `   → <img class="process-step-img" src="img/output.png">`;
            output_products_tags = convertToArray(item.output_products_tags);
            output_products_tags.forEach((tag, index) => {
                paper_md += `<div class="paper-tag">${removeUnderscores(tag)}</div>`;
            });
            paper_md += `</div>\n\n`;

            //for each item.maml.tags, include a bubble tag
            item.tags.forEach((tag, index) => {
                paper_md += `<div class="paper-tag">${removeUnderscores(tag)}</div>`;
            });

            // Add the DOI
            paper_md += `\n\n`;
            paper_md += `<a href="${item.maml.paper_id}">${item.maml.paper_id}</a>\n\n`;

            // Add the description
            paper_md += `${item.novelty}\n\n`

            // finish the encapsulation
            paper_md += `</div>\n\n`;
        }

    });

    // and close out the papers div
    paper_md += `</div>\n\n`;

    // Render the paper Markdown string to HTML and append it to #left
    let paper_html = md.render(paper_md);
    $(`#papers`).append(paper_html);

}

// and now display the spotlight process
function displayProcess(){
    // now generate a process modeler visualization markdown, based on the same JSON data, but the tea portion
    let process_md = `<div class="process">\n\n`;

    //if spotlightprocess is not defined, set it to the first paper
    if (!spotlightProcess) {
        spotlightProcess = papersJSON[0];
    }
    var item = spotlightProcess;
    process_md += `# <a href="${item.doi}" target="_blank">${item.title}</a>\n\n`;

    // the important TEA metrics
    if (item.production_costs) {
        process_md += `- Production Costs: ${item.production_costs}\n\n`;
    }
    if (item.minimal_selling_price) {
        process_md += `- Minimal Selling Price: ${item.minimal_selling_price}\n\n`;
    }
    if (item.minimal_selling_price_per_unit) {
        process_md += `- Minimal Selling Price per unit: ${item.minimal_selling_price_per_unit}\n\n`;
    }
    if (item.irr) {
        process_md += `- IRR: ${item.irr}\n\n`;
    }
    if (item.npv) {
        process_md += `- NPV: ${item.npv}\n\n`;
    }
    // display the input and output tags
    process_md += `<div class="process-tags in-out-tags"><img class="process-step-img" src="img/feedstock.png">`;
    feedstock_tags = convertToArray(item.feedstock_tags);
    feedstock_tags.forEach((tag, index) => {
        process_md += `<div class="paper-tag">${removeUnderscores(tag)}</div>`;
    });
    process_md += `   → <img class="process-step-img" src="img/output.png">`;
    output_products_tags = convertToArray(item.output_products_tags);
    output_products_tags.forEach((tag, index) => {
        process_md += `<div class="paper-tag">${removeUnderscores(tag)}</div>`;
    });
    process_md += `</div>\n\n`;

    process_md += `<div class="paper-info-expanded collapsible-content">\n\n`;
    process_md += `### Novelty\n\n${item.novelty}\n\n`;
    process_md += `### IRR\n\n${item.irr_paper}\n\n`;
    process_md += `### Price Sensitivity\n\n${item.price_sensitivity}\n\n`;
    process_md += `### Citation Count: ${item.citation_count}</div>\n\n`;

    process_md += `</div>\n\n<div class="process-tags">`;
    //for each doe tag, include a bubble tag
    item.tags.forEach((tag, index) => {
        process_md += `<div class="paper-tag">${removeUnderscores(tag)}</div>`;
    });
    process_md += `</div>\n\n`;



    if (item.maml.process_flow) {
        // console.log(item.maml.process_flow);
        var pf = item.maml.process_flow;
        pf.forEach((step, stepIndex) => {
            process_md += `<div class="process-step-title"><img class="process-step-img" src="img/step_${stepIndex + 1}.png"></img>`;
            process_md += ` Step ${stepIndex + 1}: ${removeUnderscores(step.type)}</div>\n\n`;
            process_md += `\n\n ${step.description}\n\n`;
            if (step.parameters && step.parameters.length > 0) {
                console.log(step.parameters);
                process_md += ` Parameters: `;
                step.parameters.forEach((input) => {
                    // console.log(input);
                    process_md += `${removeUnderscores(input.name)} (${input.unit}) `;
                });
            }
            process_md += `\n\nOutput: ${step.output.unit} of ${step.output.name}\n\n`;
        });
    }

    let process_html = md.render(process_md);
    if (compareProcess > 0) {
        if (compareProcess % 2 === 0) {
            $(`#right-bottom-left`).html(process_html);
        } else {
            $(`#right-bottom-right`).html(process_html);
        }
    } else {
        $(`#right-bottom-left`).html(process_html);
        $(`#right-bottom-right`).html(process_html);
    }

    // add show more after each collapsible content class
    $(".collapsible-content").after('<button class="show-more"><u>Show more</u></button><button class="show-less" style="display: none;"><u>Show less</u></button>');
    $(".show-more").click(function() {
        $(this).prev(".collapsible-content").css('height', 'auto');
        $(this).hide();
        $(this).next(".show-less").show();
    });
    // Collapse content and show "Show more" button when "Show less" is clicked
    $(".show-less").click(function() {
        $(this).prevAll(".collapsible-content").first().css('height', '6rem');
        $(this).hide();
        $(this).prev(".show-more").show();
    });
}

var graph;
var link;
var node;
var simulation;
var colors = ['#FFFF40', '#DDDF03', '#D5D703', '#C0D203', '#80B918', '#2C9348', '#027F5F'];

// Load the JSON data for the visualization demo
function loadViz(){
    // Clear the #viz SVG element
    d3.select("#viz").selectAll("*").remove();
    // create the visualization
    var feedstockGroupMap = {};
    var currentGroup = 1;
    papersJSON.forEach(paper => {
        var feedstock_tags = convertToArray(paper.feedstock_tags);
        for (var i = 0; i < feedstock_tags.length; i++) {
            var feedstock = feedstock_tags[i];
            if (!feedstockGroupMap[feedstock]) {
                feedstockGroupMap[feedstock] = currentGroup++;
            }
        }
    });

    var nodes, links = [];
    nodes = papersJSON.map(paper => {
        var feedstock_tags = convertToArray(paper.feedstock_tags);
        return {
            id: paper.id,
            feedstock_id: Math.min(...feedstock_tags.map(feedstock => feedstockGroupMap[feedstock]))
        };
    });
    // Generate links based on shared tags
    for (let i = 0; i < papersJSON.length; i++) {
        for (let j = i + 1; j < papersJSON.length; j++) {
            const sharedTagsCount = calculateSharedTags(papersJSON[i].tags, papersJSON[j].tags);
            if (sharedTagsCount > 4) {
                links.push({
                    source: papersJSON[i].id,
                    target: papersJSON[j].id,
                    value: sharedTagsCount
                });
            }
            
        }
    }

    // Create a set of node IDs that appear in the links array
    var linkedNodeIds = new Set(links.flatMap(link => [link.source, link.target]));

    // Filter the nodes array to include only nodes that appear in the links array
    nodes = papersJSON
        .filter(paper => linkedNodeIds.has(paper.id))
        .map(paper => {
            var feedstock_tags = convertToArray(paper.feedstock_tags);
            return {
                id: paper.id,
                feedstock_id: Math.min(...feedstock_tags.map(feedstock => feedstockGroupMap[feedstock]))
            };
        });

    // Group by first letter of ID
    nodes.forEach(function (node) {
        node.group = node.id.charCodeAt(0);
    });

    var svg = d3.select("#viz");
    var svgWidth = $("#viz").width();
    var svgHeight = $("#viz").height();

    svg.append("defs").selectAll("marker")
        .data(["suit", "licensing", "resolved"])
    .enter().append("marker")
        .attr("id", function(d) { return d; })
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 25)
        .attr("refY", 0)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
    .append("path")
        .attr("d", "M0,-5L10,0L0,5 L10,0 L0, -5")
        .style("stroke", "#A5A5A5")
        .style("opacity", "0.6");

        simulation = d3.forceSimulation()
        .force("link", d3.forceLink().id(function(d) { return d.id; }).distance(120)) // Increase distance between linked nodes
        .force("charge", d3.forceManyBody().strength(-40)) // Increase repulsion between nodes
        .force("center", d3.forceCenter(svgWidth / 2, svgHeight / 2));

    link = svg.append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(links)
        .enter().append("line")
        .style("marker-end",  "url(#suit)") // Modified line 
        .attr("stroke-width", function(d) { return Math.sqrt(d.value); });

    node = svg.append("g")
        .attr("class", "nodes")
        .selectAll("circle")
        .data(nodes)
        .enter().append("circle")
        .attr("r", 5)
        .attr("fill", function(d) { 
            return colors[d.feedstock_id % 7];
        })
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended))
        .on("click", function(d) {
            spotlightProcess = papersJSON.find(paper => paper.id === d.id);
            displayProcess();
            if (!hasClickedNode) hasClickedNode = true;
        })
        .on("mouseover", function(d) {
            var paperInfo = papersJSON.find(paper => paper.id === d.id);
            $("#viz-info").fadeIn(200);
            var vizInfo = `${paperInfo.title}`;
            // display the input and output tags
            vizInfo += `<div class="process-tags in-out-tags"><img class="process-step-img" src="img/feedstock.png">`;
            var feedstock_tags = convertToArray(paperInfo.feedstock_tags);
            feedstock_tags.forEach((tag, index) => {
                vizInfo += `<div class="paper-tag">${removeUnderscores(tag)}</div>`;
            });
            vizInfo += `   → <img class="process-step-img" src="img/output.png">`;
            var output_products_tags = convertToArray(paperInfo.output_products_tags);
            output_products_tags.forEach((tag, index) => {
                vizInfo += `<div class="paper-tag">${removeUnderscores(tag)}</div>`;
            });
            vizInfo += `</div>\n\n`;
            $("#viz-info").html(vizInfo);
        })
        .on("mouseout", function(d) {
            $("#viz-info").fadeOut(500);
        });

    node.append("title")
        .text(function(d) { return d.id; });

    simulation
        .nodes(nodes)
        .on("tick", ticked);

    simulation.force("link")
        .links(links);
}

function recenterViz() {
    simulation.force("center", d3.forceCenter($("#viz").width() / 2, $("#viz").height() / 2));
}


function ticked() {
    link
        .attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    node
        .attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });
}

function dragstarted(d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
}

function dragended(d) {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

// Helper function to calculate shared tags
function calculateSharedTags(tags1, tags2) {
    return tags1.filter(value => tags2.includes(value)).length;
}

function removeUnderscores(str) {
    // Replace underscores with spaces
    str = str.replace(/[_\.]/g, ' ');

    // Capitalize the first letter of each word
    str = str.toLowerCase().split(' ').map(function(word) {
        return word.charAt(0).toUpperCase() + word.slice(1);
    }).join(' ');

    return str;
}

function convertToArray(str) {
    // Replace unescaped single quotes with double quotes
    var jsonStr = str.replace(/([^\\])'/g, '$1"');

    // Replace control characters
    jsonStr = jsonStr.replace(/\\x08/g, '\\b');

    // Parse the JSON string into an array
    var arr = JSON.parse(jsonStr);
    return arr;
}