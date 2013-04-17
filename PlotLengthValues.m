function PlotLengthValues(OutputFolder)

FiberLengthValues = load([OutputFolder '/FiberLengths.txt']);
FiberLengthValues=FiberLengthValues';

x=1:24;
plot(x,FiberLengthValues(4,:),'r+',x,FiberLengthValues(3,:),'g+',x,FiberLengthValues(2,:),'b+');
legend('Average over 75 percentile Fiber Lengths','75 percentile Fiber Lengths','Average Fiber Lengths');
set(gca, 'XTick', x );
set(gca, 'XTickLabel', FiberLengthValues(1,:) );
xlabel('Measurement Frame');
ylabel('Fiber Length Mesure');

saveas(gca, [OutputFolder '/FiberLengths.png'], 'png') % gca is the current figure

exit
